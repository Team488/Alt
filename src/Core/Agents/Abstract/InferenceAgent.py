"""
Base agent for running machine learning inference on camera frames.

This module provides the InferenceAgent class which extends CameraUsingAgentBase to add
inference capabilities. It integrates with the MultiInferencer to support various
inference backends and models for object detection and classification on camera frames.

The module also provides a convenient factory function (InferenceAgentPartial) to create
partially initialized agents that can be completed at runtime.
"""

import os
import cv2
import time
from functools import partial
from typing import Optional, Dict, Any, List, Tuple

import numpy as np

# from JXTABLES.XDashDebugger import XDashDebugger

from Core.Agents.Abstract.CameraUsingAgentBase import CameraUsingAgentBase
from abstract.Capture import Capture, ConfigurableCapture
from inference.MultiInferencer import MultiInferencer
from tools.Constants import CameraIntrinsics, InferenceMode
from coreinterface.FramePacket import FramePacket


class InferenceAgent(CameraUsingAgentBase):
    """
    Agent that performs machine learning inference on camera frames.
    
    This agent extends CameraUsingAgentBase to add inference capabilities using
    the MultiInferencer, which supports various inference backends. It processes
    camera frames to perform object detection or classification and makes the
    results available for derived classes to use.
    
    Class Hierarchy:
        Agent -> CameraUsingAgentBase -> InferenceAgent
    
    Attributes:
        inferenceMode: The mode of inference to perform (YOLO, etc.)
        inf: MultiInferencer instance used to run the models
        confidence: Property for the confidence threshold setting
        drawBoxes: Property for whether to draw bounding boxes on frames
        results: Dictionary containing the most recent inference results
        
    Note:
        Requires extra arguments passed in either using functools.partial or by
        extending the class. See InferenceAgentPartial for a convenient factory function.
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the InferenceAgent with required parameters.
        
        Args:
            **kwargs: Keyword arguments including:
                inferenceMode: The inference mode to use (YOLO, etc.)
                (other arguments are passed to the parent class)
        """
        super().__init__(**kwargs)
        self.inferenceMode: Optional[InferenceMode] = kwargs.get("inferenceMode", None)
        self.inf: Optional[MultiInferencer] = None
        self.confidence = None
        self.drawBoxes = None
        self.results: Optional[Dict[str, Any]] = None

    def create(self) -> None:
        """
        Initialize the inferencer and create required properties.
        
        This method sets up the MultiInferencer with the specified inference mode and
        creates properties for controlling the inference process (confidence threshold
        and whether to draw bounding boxes).
        
        Raises:
            ValueError: If inferenceMode or propertyOperator is not properly initialized
        """
        super().create()
        if self.Sentinel:
            self.Sentinel.info("Creating Frame Processor...")
            
        if self.inferenceMode is None:
            raise ValueError("InferenceMode not provided")
            
        self.inf = MultiInferencer(
            inferenceMode=self.inferenceMode,
        )
        
        if self.propertyOperator is None:
            raise ValueError("PropertyOperator not initialized")
            
        self.confidence = self.propertyOperator.createProperty(
            "Confidence_Threshold", 0.7
        )
        self.drawBoxes = self.propertyOperator.createProperty("Draw_Boxes", True)

    def runPeriodic(self) -> None:
        """
        Run machine learning inference on the latest camera frame.
        
        This method performs inference on the latest camera frame using the configured
        MultiInferencer. It applies the current confidence threshold and drawing settings.
        The results are stored in the results attribute for derived classes to access.
        
        Raises:
            ValueError: If required components (timer, inferencer, properties) are not initialized
        """
        super().runPeriodic()
        
        if self.timer is None:
            raise ValueError("Timer not initialized")
            
        if self.inf is None:
            raise ValueError("Inferencer not initialized")
            
        if self.latestFrameMain is None:
            return
            
        if self.confidence is None or self.drawBoxes is None:
            raise ValueError("Properties not initialized")

        with self.timer.run("inference"):
            self.results = self.inf.run(
                self.latestFrameMain, self.confidence.get(), self.drawBoxes.get()
            )

    def getName(self) -> str:
        """
        Get the name of this agent.
        
        Returns:
            String identifying this agent type
        """
        return "Inference_Agent_Process"

    def getDescription(self) -> str:
        """
        Get a description of what this agent does.
        
        Returns:
            String description of the agent's functionality
        """
        return "Ingest_Camera_Run_Ai_Model"


def InferenceAgentPartial(
    capture: ConfigurableCapture,
    inferenceMode: InferenceMode,
    showFrames: bool = False,
) -> Any:
    """
    Factory function that returns a partially initialized InferenceAgent.
    
    This function creates a partial InferenceAgent with the necessary parameters
    pre-configured, making it easy to instantiate and register with Neo. The returned
    partial function can be passed directly to Neo for agent registration.
    
    Args:
        capture: The camera capture device to use for frames
        inferenceMode: The inference mode to use (YOLO, etc.)
        showFrames: Whether to display camera frames (default: False)
        
    Returns:
        A partially initialized InferenceAgent constructor that can be passed to Neo
    """
    return partial(
        InferenceAgent,
        capture=capture,
        cameraIntrinsics=capture.getIntrinsics(),
        inferenceMode=inferenceMode,
        showFrames=showFrames,
    )
