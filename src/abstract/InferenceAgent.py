import os
import cv2
import time
from functools import partial

import numpy as np

# from JXTABLES.XDashDebugger import XDashDebugger

from abstract.Agent import Agent
from inference.MultiInferencer import MultiInferencer
from tools.Constants import InferenceMode
from coreinterface.FramePacket import FramePacket


class InferenceAgent(Agent):
    """Agent -> InferenceAgent
    Adds inference capabilites to an agent, processing frames
    NOTE: Requires extra arguments passed in somehow, for example using Functools partial or extending the class"""

    FRAMEPOSTFIX = "Frame"

    def __init__(
        self,
        cameraPath: str,
        inferenceMode: InferenceMode,
    ):
        self.cameraPath = cameraPath
        self.inferenceMode = inferenceMode

    def create(self):
        super().create()
        self.cap = cv2.VideoCapture(self.cameraPath)
        retTest = True
        if self.cap.isOpened():
            retTest, _ = self.cap.read()

        if not self.cap.isOpened() or not retTest:
            raise BrokenPipeError("Failed to open camera!")

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
        with self.timer.run("cap_read"):
            ret, frame = self.cap.read()

        if ret:
            with self.timer.run("inference"):
                self.results = self.inf.run(frame,self.confidence.get(),self.drawBoxes.get())
            
            framepkt = FramePacket.createPacket(time.time(),"helooo",frame)
            self.frameProp.set(framepkt.to_bytes())
        else:
            self.Sentinel.error("Opencv Cap ret is false!")
            if self.cap.isOpened():
                self.cap.release()
            raise BrokenPipeError("Camera returned false!")
            # will close cap

    def onClose(self):
        super().onClose()
        if self.cap.isOpened():
            self.cap.release()

    def isRunning(self):
        if not self.cap.isOpened():
            self.Sentinel.fatal("Camera cant be opened!")
            return False
        return True

    def forceShutdown(self):
        super().forceShutdown()
        self.cap.release()

    def getName(self):
        return "Inference_Agent_Process"

    def getDescription(self):
        return "Ingest_Camera_Run_Ai_Model"

    def getIntervalMs(self):
        return 0


def InferenceAgentPartial(
    cameraPath, inferenceMode : InferenceMode
):
    """Returns a partially completed frame processing agent. All you have to do is pass it into neo"""
    return partial(
        InferenceAgent,
        cameraPath=cameraPath,
        inferenceMode=inferenceMode,
    )
