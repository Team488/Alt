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
    """Agent -> CameraUsingAgentBase -> InferenceAgent
    Adds inference capabilites to an agent, processing frames
    NOTE: Requires extra arguments passed in somehow, for example using Functools partial or extending the class"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.inferenceMode: Optional[InferenceMode] = kwargs.get("inferenceMode", None)
        self.inf: Optional[MultiInferencer] = None
        self.confidence = None
        self.drawBoxes = None
        self.results: Optional[Dict[str, Any]] = None

    def create(self) -> None:
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
        return "Inference_Agent_Process"

    def getDescription(self) -> str:
        return "Ingest_Camera_Run_Ai_Model"


def InferenceAgentPartial(
    capture: ConfigurableCapture,
    inferenceMode: InferenceMode,
    showFrames: bool = False,
) -> Any:
    """Returns a partially completed frame processing agent. All you have to do is pass it into neo"""
    return partial(
        InferenceAgent,
        capture=capture,
        inferenceMode=inferenceMode,
        showFrames=showFrames,
    )
