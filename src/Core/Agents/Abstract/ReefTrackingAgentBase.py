"""
Reef Tracking Agent Base Module - For tracking coral reef elements and AprilTags

This module provides the ReefTrackingAgentBase class, which extends the CameraUsingAgentBase
to add specialized reef tracking capabilities. It detects and tracks coral, algae, and
AprilTag markers in the underwater environment, processing visual data to determine 
the relative position and orientation of reef elements.

Key features:
- Detection and tracking of coral elements using color-based methods
- Detection and tracking of algae using specialized algorithms
- AprilTag recognition for precise positioning and orientation
- Integration with pose solving to determine 3D positions
- Publishing tracking results to other system components
- Support for both visual display and network telemetry

This class forms the foundation for agents that need to monitor and interact with
the underwater reef environment.
"""

import datetime
from functools import partial
import math
import time
from typing import Optional, List, Tuple, Dict, Any, Callable, Union

import cv2
import numpy as np

from Core.Agents.Abstract.CameraUsingAgentBase import CameraUsingAgentBase
from abstract.Capture import ConfigurableCapture
from reefTracking import reefTracker
from reefTracking.reefTracker import ReefTracker
from reefTracking.poseSolver import poseSolver
from tools.Constants import ATLocations, CameraExtrinsics, CameraIntrinsics
from coreinterface.ReefPacket import ReefPacket
from tools.Units import LengthType


class ReefTrackingAgentBase(CameraUsingAgentBase):
    """
    Base class for agents that track reef elements and AprilTags.
    
    This class extends CameraUsingAgentBase to add specialized reef tracking
    capabilities. It processes camera frames to detect and track coral, algae,
    and AprilTag markers in the underwater environment.
    
    The inheritance hierarchy is:
    Agent -> CameraUsingAgentBase -> ReefTrackingAgentBase
    
    Attributes:
        OBSERVATIONPOSTFIX: String used for network updates of reef observations
        cameraIntrinsics: Camera calibration parameters
        poseSolver: Component for solving 3D poses from 2D detections
        tracker: Component that implements reef element detection algorithms
        latestPoseREEF: Most recent pose estimate for the reef
        
    Notes:
        - This agent must be created using the partial function pattern
        - If showFrames is True, this agent must run on the main thread
    """
    OBSERVATIONPOSTFIX: str = "OBSERVATIONS"

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a new ReefTrackingAgentBase instance.
        
        Args:
            **kwargs: Keyword arguments that must include:
                cameraIntrinsics: Camera calibration parameters
                And other arguments required by parent classes
        """
        super().__init__(**kwargs)
        self.cameraIntrinsics: Optional[CameraIntrinsics] = kwargs.get("cameraIntrinsics", None)
        self.poseSolver: Optional[poseSolver] = None
        self.tracker: Optional[ReefTracker] = None
        self.latestPoseREEF: Optional[Dict[str, Any]] = None

    def create(self) -> None:
        """
        Initialize reef tracking components.
        
        This method is called during agent initialization and sets up the
        pose solver and reef tracker components. It also publishes tracker
        configuration information to the network property system.
        
        Raises:
            ValueError: If required components are missing
        """
        super().create()
        
        if self.cameraIntrinsics is None:
            raise ValueError("CameraIntrinsics not provided")
            
        self.poseSolver = poseSolver()
        self.tracker = ReefTracker(cameraIntrinsics=self.cameraIntrinsics)

        self.putNetworkInfo()

    def putNetworkInfo(self) -> None:
        """
        Publish tracker configuration information to the network property system.
        
        This method publishes timestamps for the various histogram data files
        used by the reef tracker. These timestamps help verify that the correct
        histogram data is being used for detection.
        
        Raises:
            ValueError: If PropertyOperator is not initialized
        """
        if self.propertyOperator is None:
            raise ValueError("PropertyOperator not initialized")
            
        getReadable: Callable[[float], str] = lambda time: datetime.datetime.fromtimestamp(time).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        purpleHistMtime = reefTracker.purpleHistMTime
        whiteHistMtime = reefTracker.whiteHistMTime
        algaeHistMtime = reefTracker.algaeHistMTime

        self.propertyOperator.createReadOnlyProperty(
            "ReefTracker.PurpleReefPostHist.TimeStamp", getReadable(purpleHistMtime)
        )
        self.propertyOperator.createReadOnlyProperty(
            "ReefTracker.WhiteCoralHist.TimeStamp", getReadable(whiteHistMtime)
        )
        self.propertyOperator.createReadOnlyProperty(
            "ReefTracker.AlgaeHist.TimeStamp", getReadable(algaeHistMtime)
        )

    def runPeriodic(self) -> None:
        """
        Execute the agent's periodic processing logic.
        
        This method is called regularly by the agent framework and performs the
        following operations:
        1. Processes the latest camera frame for reef elements and AprilTags
        2. Calculates 3D pose estimates from the detections
        3. Creates a packet with the detection results
        4. Publishes the packet to the network property system
        
        The method requires a valid camera frame and properly initialized
        tracking components to function.
        
        Raises:
            ValueError: If required components are not initialized
        """
        super().runPeriodic()
        
        if self.tracker is None:
            raise ValueError("Tracker not initialized")
            
        if self.poseSolver is None:
            raise ValueError("PoseSolver not initialized")
            
        if self.updateOp is None:
            raise ValueError("UpdateOperator not initialized")
            
        if self.latestFrameMain is None:
            return
            
        # Process the latest frame to detect coral, algae and AprilTags
        outCoral, outAlgae, atOutput = self.tracker.getAllTracks(
            self.latestFrameMain, drawBoxes=self.showFrames or self.sendFrame
        )
        # Calculate 3D pose estimate from AprilTag detections
        self.latestPoseREEF = self.poseSolver.getLatestPoseEstimate(atOutput)

        # Create and publish packet with detection results
        reefPkt = ReefPacket.createPacket(
            outCoral, outAlgae, "helloo", time.time() * 1000
        )
        self.updateOp.addGlobalUpdate(self.OBSERVATIONPOSTFIX, reefPkt.to_bytes())

    def getName(self) -> str:
        """
        Get the agent's name for identification.
        
        Returns:
            String identifier for this agent type
        """
        return "Reef_Tracking_Agent"

    def getDescription(self) -> str:
        """
        Get a human-readable description of this agent's functionality.
        
        Returns:
            String description of what this agent does
        """
        return "Gets_Reef_State"


def ReefTrackingAgentPartial(capture: ConfigurableCapture, showFrames: bool = False) -> Any:
    """
    Create a partially configured reef tracking agent.
    
    This helper function creates a partially initialized reef tracking agent
    that can be passed directly to Neo for execution. It automatically sets up
    the agent with the given capture device and configuration parameters.
    
    Args:
        capture: Camera capture device to use for image acquisition
        showFrames: Whether to display processed frames with detections
        
    Returns:
        A partially configured ReefTrackingAgentBase that can be passed to Neo
    """
    return partial(
        ReefTrackingAgentBase,
        capture=capture,
        cameraIntrinsics=capture.getIntrinsics(),
        showFrames=showFrames,
    )
