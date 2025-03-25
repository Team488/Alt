"""
Object Localizing Agent Base Module - For detecting and spatially localizing objects

This module provides the ObjectLocalizingAgentBase class, which extends the 
TimestampRegulatedAgentBase to add object detection and spatial localization 
capabilities. It processes camera frames through machine learning models and
converts 2D detections to 3D world coordinates using camera calibration parameters.

Key features:
- Integration with various machine learning inference models
- Converting pixel coordinates to world coordinates
- Applying camera calibration for accurate spatial localization
- Publishing detection results to other system components
- Support for both regular and depth-sensing cameras
- Helper function for creating pre-configured agent instances

This class forms the foundation for all agents that perform object detection
and localization tasks in the system.
"""

import math
import os
from typing import Union, Optional, List, Tuple, Any
import cv2
import time
from functools import partial

import numpy as np

# from JXTABLES.XDashDebugger import XDashDebugger

from Core.Agents.Abstract.TimestampRegulatedAgentBase import TimestampRegulatedAgentBase
from abstract.Capture import Capture, ConfigurableCapture
from abstract.depthCamera import depthCamera
from coreinterface.DetectionPacket import DetectionPacket
from tools.Constants import InferenceMode, CameraExtrinsics, CameraIntrinsics
from mapinternals.localFrameProcessor import LocalFrameProcessor
import Core


class ObjectLocalizingAgentBase(TimestampRegulatedAgentBase):
    """
    Object detection and localization agent base class.
    
    This agent extends the TimestampRegulatedAgentBase to add object detection
    and spatial localization capabilities. It processes camera frames through 
    a machine learning model and converts 2D detections to 3D world coordinates
    using camera calibration parameters.
    
    The inheritance hierarchy is:
    Agent -> (CameraUsingAgentBase, PositionLocalizingAgentBase) -> 
    TimestampRegulatedAgentBase -> ObjectLocalizingAgentBase
    
    Attributes:
        DETECTIONPOSTFIX: String used to create detection update keys
        cameraIntrinsics: Camera intrinsic parameters (focal length, optical center)
        cameraExtrinsics: Camera extrinsic parameters (position, orientation)
        inferenceMode: Type of machine learning model being used
        frameProcessor: Processing system for object detection and localization
        
    Notes:
        Requires additional arguments to be passed in, either by using functools.partial
        or by extending the class.
    """

    DETECTIONPOSTFIX = "Detections"

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a new ObjectLocalizingAgentBase instance.
        
        Args:
            **kwargs: Keyword arguments that must include:
                cameraIntrinsics: Camera intrinsic parameters
                cameraExtrinsics: Camera extrinsic parameters
                inferenceMode: Type of inference model to use
                And other arguments required by parent classes
        """
        self.cameraIntrinsics: Optional[CameraIntrinsics] = kwargs.get("cameraIntrinsics", None)
        self.cameraExtrinsics: Optional[CameraExtrinsics] = kwargs.get("cameraExtrinsics", None)
        self.inferenceMode: Optional[InferenceMode] = kwargs.get("inferenceMode", None)
        self.frameProcessor: Optional[LocalFrameProcessor] = None
        super().__init__(**kwargs)

    def create(self) -> None:
        """
        Initialize the object localization system.
        
        This method:
        1. Verifies that required components are available
        2. Checks that the inference mode matches any existing core inference mode
        3. Creates the frame processor using camera calibration and inference settings
        
        Raises:
            ValueError: If required components are missing
            Exception: If there's a model type mismatch with the core system
        """
        super().create()
        # self.xdashDebugger = XDashDebugger()
        if self.Sentinel is None:
            raise ValueError("Logger not initialized")
            
        if self.xclient is None:
            raise ValueError("XTablesClient not initialized")
            
        self.Sentinel.info("Creating Frame Processor...")
        currentCoreINFName = self.xclient.getString(Core.COREMODELTABLE)
        currentCoreINFMode = InferenceMode.getFromName(currentCoreINFName, default=None)
        
        if self.inferenceMode is None:
            raise ValueError("InferenceMode not provided")
            
        if currentCoreINFMode is not None:
            # assert you are running same model type as any current core process
            isMatch = InferenceMode.assertModelType(
                currentCoreINFMode, self.inferenceMode
            )
            if not isMatch:
                self.Sentinel.fatal(
                    f"Model type mismatch!: Core is Running: {currentCoreINFMode.getModelType()} This is running {self.inferenceMode.getModelType()}"
                )
                raise Exception(
                    f"Model type mismatch!: Core is Running: {currentCoreINFMode.getModelType()} This is running {self.inferenceMode.getModelType()}"
                )
            else:
                self.Sentinel.fatal(f"Model type matched!")
        else:
            self.Sentinel.warning(
                "Was not able to get core model type! Make sure you match!"
            )

        if self.cameraIntrinsics is None:
            raise ValueError("CameraIntrinsics not provided")
            
        if self.cameraExtrinsics is None:
            raise ValueError("CameraExtrinsics not provided")
            
        self.frameProcessor = LocalFrameProcessor(
            cameraIntrinsics=self.cameraIntrinsics,
            cameraExtrinsics=self.cameraExtrinsics,
            inferenceMode=self.inferenceMode,
            depthMode=self.depthEnabled,
        )

    def runPeriodic(self) -> None:
        """
        Process the latest camera frame to detect and localize objects.
        
        This method is called periodically and performs the following steps:
        1. Verifies all required components are available
        2. Applies position offsets to the robot's current pose
        3. Processes the latest camera frame through the object detection model
        4. Creates a detection packet with the processed results
        5. Publishes the detections through the update system
        
        Raises:
            ValueError: If any required components are missing
        """
        super().runPeriodic()
        
        if self.timer is None:
            raise ValueError("Timer not initialized")
            
        if self.frameProcessor is None:
            raise ValueError("Frame processor not initialized")
            
        if self.updateOp is None:
            raise ValueError("UpdateOperator not initialized")
            
        if self.Sentinel is None:
            raise ValueError("Logger not initialized")
            
        if self.positionOffsetXM is None or self.positionOffsetYM is None or self.positionOffsetYAWDEG is None:
            raise ValueError("Position offset properties not initialized")
            
        sendFrame = self.sendFrame
        offsetXCm = self.positionOffsetXM.get() * 100
        offsetYCm = self.positionOffsetYM.get() * 100
        offsetYawRAD = math.radians(self.positionOffsetYAWDEG.get())
        
        if self.latestFrameMain is None:
            self.Sentinel.warning("No latest color frame available")
            return
            
        with self.timer.run("frame-processing"):
            processedResults = self.frameProcessor.processFrame(
                self.latestFrameMain,
                self.latestFrameDEPTH if self.depthEnabled else None,
                robotPosXCm=self.robotPose2dCMRAD[0] + offsetXCm,
                robotPosYCm=self.robotPose2dCMRAD[1] + offsetYCm,
                robotYawRad=self.robotPose2dCMRAD[2] + offsetYawRAD,
                drawBoxes=sendFrame or self.showFrames,
                # if you are sending frames, you likely want to see bounding boxes aswell
            )

        # add highest detection telemetry
        # if processedResults:
        #     best_idx = max(
        #         range(len(processedResults)), key=lambda i: processedResults[i][2]
        #     )
        #     best_result = processedResults[best_idx]
        #     x, y, z = best_result[1]
        #     self.propertyOperator.createReadOnlyProperty(
        #         "BestResult.BestX", ""
        #     ).set(float(x))
        #     self.propertyOperator.createReadOnlyProperty(
        #         "BestResult.BestY", ""
        #     ).set(float(y))
        #     self.propertyOperator.createReadOnlyProperty(
        #         "BestResult.BestZ", ""
        #     ).set(float(z))

        timestampMs = time.time() * 1000

        detectionPacket = DetectionPacket.createPacket(
            processedResults, "Detection", timestampMs
        )
        self.updateOp.addGlobalUpdate(self.DETECTIONPOSTFIX, detectionPacket.to_bytes())

        # optionally send frame
        self.Sentinel.info("Processed frame!")

    def getName(self) -> str:
        """
        Get the agent's name for identification.
        
        Returns:
            String identifier for this agent type
        """
        return "Object_Localizer"

    def getDescription(self) -> str:
        """
        Get a human-readable description of this agent's functionality.
        
        Returns:
            String description of what this agent does
        """
        return "Inference_Then_Localize"

    def getIntervalMs(self) -> int:
        """
        Get the recommended periodic execution interval in milliseconds.
        
        Returns:
            The interval in milliseconds (0 means run as fast as possible)
        """
        return 0


def ObjectLocalizingAgentPartial(
    capture: Union[depthCamera, ConfigurableCapture],
    cameraExtrinsics: CameraExtrinsics,
    inferenceMode: InferenceMode,
    showFrames: bool = False,
) -> Any:
    """
    Create a partially configured object localization agent.
    
    This helper function creates a partially initialized object localization agent
    that can be passed directly to Neo for execution. It automatically sets up
    the agent with the given capture device and configuration parameters.
    
    Args:
        capture: Camera capture device to use for image acquisition
        cameraExtrinsics: Camera position and orientation parameters
        inferenceMode: Type of inference model to use
        showFrames: Whether to display processed frames with detections
        
    Returns:
        A partially configured ObjectLocalizingAgentBase that can be passed to Neo
    """
    return partial(
        ObjectLocalizingAgentBase,
        capture=capture,
        cameraIntrinsics=capture.getIntrinsics(),
        cameraExtrinsics=cameraExtrinsics,
        inferenceMode=inferenceMode,
        showFrames=showFrames,
    )
