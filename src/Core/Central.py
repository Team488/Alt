"""
Central Module - Core coordination and state management for the Alt system.

This module provides the Central class, which serves as the central coordination
and state management component for the Alt system. It maintains the global state
of detected objects, reef elements, and provides interfaces for path planning
and tracking.

The Central class integrates various subsystems including:
- Object detection and tracking using Kalman filters
- Probabilistic mapping of objects and obstacles
- Reef state tracking
- Path planning and generation
- Configuration and property management

It processes updates from multiple camera sources and reef detections,
maintaining a consistent world model that can be used by agents for decision making.
"""

import numpy as np
import cv2
from logging import Logger
from mapinternals.UKF import Ukf
from tools.Constants import InferenceMode, MapConstants, CameraIdOffsets2024
from mapinternals.probmap import ProbMap
from mapinternals.KalmanLabeler import KalmanLabeler
from mapinternals.KalmanCache import KalmanCache
from pathplanning.PathGenerator import PathGenerator
from reefTracking.ReefState import ReefState
from Core.ConfigOperator import ConfigOperator
from Core.PropertyOperator import PropertyOperator


class Central:
    """
    Central coordination and state management for the Alt system.
    
    This class serves as the central hub for system state, integrating various
    subsystems including object detection/tracking, probabilistic mapping,
    reef state tracking, and path planning. It maintains the global state
    of detected objects and reef elements, providing a consistent world model
    for decision making.
    
    Attributes:
        Sentinel (Logger): Logger for recording system activities and errors
        configOp (ConfigOperator): Configuration management interface
        propertyOp (PropertyOperator): Property management interface
        inferenceMode (InferenceMode): Current inference configuration
        labels (list): Object labels that can be detected
        useObstacles (Property): Flag indicating if obstacle avoidance is enabled
        kalmanCaches (list): List of Kalman filter caches for each object type
        objectmap (ProbMap): Probabilistic map of detected objects
        reefState (ReefState): Current state of reef elements
        ukf (Ukf): Unscented Kalman Filter for state estimation
        labler (KalmanLabeler): Component for tracking and labeling objects
        obstacleMap (np.ndarray): Map of static obstacles in the environment
        pathGenerator (PathGenerator): Component for generating robot paths
    """
    def __init__(
        self,
        logger: Logger,
        configOp: ConfigOperator,
        propertyOp: PropertyOperator,
        inferenceMode: InferenceMode,
    ) -> None:
        """
        Initialize the Central coordination system.
        
        Args:
            logger: Logger for recording activities and errors
            configOp: Configuration management interface
            propertyOp: Property management interface
            inferenceMode: Current inference configuration
        """
        self.Sentinel = logger
        self.configOp = configOp
        self.propertyOp = propertyOp
        self.inferenceMode = inferenceMode
        self.labels = self.inferenceMode.getLabels()

        self.useObstacles = self.propertyOp.createProperty("Use_Obstacles", True)

        # Initialize subsystems
        self.kalmanCaches = [KalmanCache() for _ in self.labels]
        self.objectmap = ProbMap(self.labels)
        self.reefState = ReefState()
        self.ukf = Ukf()
        self.labler = KalmanLabeler(self.kalmanCaches, self.labels)
        self.obstacleMap = self.__tryLoadObstacleMap()
        self.pathGenerator = PathGenerator(self.objectmap, self.obstacleMap)

    def __tryLoadObstacleMap(self):
        """
        Try to load the obstacle map from configuration.
        
        This private method attempts to load the obstacle map from the configuration.
        If loading fails or obstacles are disabled, it returns a default empty map.
        
        Returns:
            np.ndarray: Boolean array representing obstacle locations
        """
        defaultMap = np.zeros(
            (MapConstants.fieldWidth.value, MapConstants.fieldHeight.value), dtype=bool
        )
        if self.useObstacles.get():
            obstacleMap = self.configOp.getContent("obstacleMap.npy")
            if obstacleMap is not None:
                return obstacleMap
            else:
                # this will never happen, as we have the obstaclemap in assets too
                self.Sentinel.warning(
                    "Failed to load obstacles, defaulting to empty map"
                )

        return defaultMap

    def processReefUpdate(
        self,
        reefResults: tuple[list[tuple[int, int, float]], list[tuple[int, float]]],
        timeStepMs,
    ) -> None:
        """
        Process updates about reef elements (coral and algae).
        
        This method updates the reef state based on new observations of coral
        and algae elements. It handles time-based dissipation of confidence
        and updates the reef state with new observations.
        
        Args:
            reefResults: A tuple containing:
                - List of coral observations (tuples of apriltag ID, branch ID, and confidence)
                - List of algae observations (tuples of apriltag ID and confidence)
            timeStepMs: Time step in milliseconds since the last update
        """
        self.reefState.dissipateOverTime(timeStepMs)

        for reefResult in reefResults:
            coralObservation, algaeObservation = reefResult
            for apriltagid, branchid, opennessconfidence in coralObservation:
                self.reefState.addObservationCoral(
                    apriltagid, branchid, opennessconfidence
                )

            for apriltagid, opennessconfidence in algaeObservation:
                self.reefState.addObservationAlgae(apriltagid, opennessconfidence)

    def processFrameUpdate(
        self,
        cameraResults: list[
            tuple[
                list[
                    list[int, tuple[int, int, int], float, bool, np.ndarray],
                    int,
                ]
            ]
        ],
        timeStepMs,
    ) -> None:
        """
        Process object detection updates from camera frames.
        
        This method updates the object map and tracking state based on new
        object detections from camera frames. It handles time-based dissipation
        of confidence, updates the Kalman filters, and adds the filtered
        detections to the object map.
        
        Args:
            cameraResults: List of camera results, where each result is a tuple of:
                - List of detections, where each detection is:
                  [id, (x,y,z), confidence, class_index, features]
                - ID offset for the camera
            timeStepMs: Time step in milliseconds since the last update
        """
        # Dissipate probabilities at start of iteration
        self.objectmap.disspateOverTime(timeStepMs)

        # Process each camera's detections
        for singleCamResult, idOffset in cameraResults:
            if singleCamResult:
                # Update object IDs based on tracking
                self.labler.updateRealIds(singleCamResult, idOffset, timeStepMs)
                (id, coord, prob, class_idx, features) = singleCamResult[0]
                (x, y, z) = coord

                # Load data into Kalman filter
                # If object is new, UKF will initialize a new state
                self.kalmanCaches[class_idx].LoadInKalmanData(id, x, y, self.ukf)

                # Predict new state using Kalman filter
                newState = self.ukf.predict_and_update([x, y])

                # Save updated Kalman filter state back to cache
                self.kalmanCaches[class_idx].saveKalmanData(id, self.ukf)

                # Add filtered detection to probability map
                self.objectmap.addDetectedObject(
                    class_idx, int(newState[0]), int(newState[1]), prob
                )
