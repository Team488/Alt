import os
import cv2
import time
from functools import partial

import numpy as np

# from JXTABLES.XDashDebugger import XDashDebugger

from Core.Agents.Abstract.CameraUsingAgentBase import CameraUsingAgentBase
from inference.MultiInferencer import MultiInferencer
from tools.Constants import CameraIntrinsics, InferenceMode
from coreinterface.FramePacket import FramePacket


class InferenceAgent(CameraUsingAgentBase):
    """Agent -> CameraUsingAgentBase -> InferenceAgent
    Adds inference capabilites to an agent, processing frames
    NOTE: Requires extra arguments passed in somehow, for example using Functools partial or extending the class"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.inferenceMode = kwargs.get("inferenceMode", None)

    def create(self):
        super().create()
        self.Sentinel.info("Creating Frame Processor...")
        self.inf = MultiInferencer(
            inferenceMode=self.inferenceMode,
        )
        self.confidence = self.propertyOperator.createProperty(
            "Confidence_Threshold", 0.7
        )
        self.drawBoxes = self.propertyOperator.createProperty("Draw_Boxes", True)

    def runPeriodic(self):
        super().runPeriodic()

        with self.timer.run("inference"):
            self.results = self.inf.run(
                self.latestFrame, self.confidence.get(), self.drawBoxes.get()
            )

    def getName(self):
        return "Inference_Agent_Process"

    def getDescription(self):
        return "Ingest_Camera_Run_Ai_Model"


def InferenceAgentPartial(
    cameraPath,
    cameraIntrinsics: CameraIntrinsics,
    inferenceMode: InferenceMode,
    showFrames: bool = False,
):
    """Returns a partially completed frame processing agent. All you have to do is pass it into neo"""
    return partial(
        InferenceAgent,
        cameraPath=cameraPath,
        cameraIntrinsics=cameraIntrinsics,
        inferenceMode=inferenceMode,
        showFrames=showFrames,
    )
