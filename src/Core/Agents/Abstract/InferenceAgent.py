import os
import cv2
import time
from functools import partial

import numpy as np

# from JXTABLES.XDashDebugger import XDashDebugger

from Core.Agents.Abstract.CameraUsingAgentBase import CameraUsingAgentBase
from inference.MultiInferencer import MultiInferencer
from tools.Constants import InferenceMode
from coreinterface.FramePacket import FramePacket


class InferenceAgent(CameraUsingAgentBase):
    """Agent -> CameraUsingAgentBase -> InferenceAgent
    Adds inference capabilites to an agent, processing frames
    NOTE: Requires extra arguments passed in somehow, for example using Functools partial or extending the class"""

    FRAMEPOSTFIX = "Frame"

    def __init__(
        self,
        cameraPath: str,
        inferenceMode: InferenceMode,
    ):
        super().__init__(cameraPath)
        self.inferenceMode = inferenceMode

    def create(self):
        super().create()
        self.Sentinel.info("Creating Frame Processor...")
        self.inf = MultiInferencer(
            inferenceMode=self.inferenceMode,
        )
        self.confidence = self.propertyOperator.createProperty("Confidence_Threshold",0.7)
        self.drawBoxes = self.propertyOperator.createProperty("Draw_Boxes",True)

        self.frameProp = self.propertyOperator.createCustomReadOnlyProperty(
            self.FRAMEPOSTFIX, b""
        )

    def runPeriodic(self):
        super().runPeriodic()
        
        with self.timer.run("inference"):
            self.results = self.inf.run(self.latestFrame,self.confidence.get(),self.drawBoxes.get())
        
        framepkt = FramePacket.createPacket(time.time(),"helooo",self.latestFrame)
        self.frameProp.set(framepkt.to_bytes())


    def getName(self):
        return "Inference_Agent_Process"

    def getDescription(self):
        return "Ingest_Camera_Run_Ai_Model"


def InferenceAgentPartial(
    cameraPath, inferenceMode : InferenceMode
):
    """Returns a partially completed frame processing agent. All you have to do is pass it into neo"""
    return partial(
        InferenceAgent,
        cameraPath=cameraPath,
        inferenceMode=inferenceMode,
    )
