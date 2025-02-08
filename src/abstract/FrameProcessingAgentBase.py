import os
import cv2
import time
from functools import partial

import numpy as np
from JXTABLES.XDashDebugger import XDashDebugger

from abstract.LocalizingAgentBase import LocalizingAgentBase
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.FramePacket import FramePacket
from tools.Constants import InferenceMode, CameraExtrinsics, CameraIntrinsics
from mapinternals.localFrameProcessor import LocalFrameProcessor


class FrameProcessingAgent(LocalizingAgentBase):
    """Agent -> LocalizingAgentBase -> FrameProcessingAgentBase

    Adds inference capabilites to an agent, processing frames and sending detections
    NOTE: Requires extra arguments passed in somehow, for example using Functools partial"""

    DETECTIONPOSTFIX = "Detections"
    FRAMEPOSTFIX = "Frame"

    def __init__(
        self,
        central,
        xclient,
        propertyOperator,
        configOperator,
        shareOperator,
        logger,
        cameraPath: str,
        cameraIntrinsics: CameraIntrinsics,
        cameraExtrinsics: CameraExtrinsics,
        inferenceMode: InferenceMode,
    ):
        super().__init__(
            central, xclient, propertyOperator, configOperator, shareOperator, logger
        )
        self.cameraPath = cameraPath
        self.cameraIntrinsics = cameraIntrinsics
        self.cameraExtrinsics = cameraExtrinsics
        self.inferenceMode = inferenceMode

    def create(self):
        super().create()
        self.xdashDebugger = XDashDebugger()
        self.cap = cv2.VideoCapture(self.cameraPath)
        if not self.cap.isOpened():
            raise BrokenPipeError("Failed to open camera!")

        self.Sentinel.info("Creating Frame Processor...")
        self.frameProcessor = LocalFrameProcessor(
            cameraIntrinsics=self.cameraIntrinsics,
            cameraExtrinsics=self.cameraExtrinsics,
            inferenceMode=self.inferenceMode,
        )
        self.frameProp = self.propertyOperator.createCustomReadOnlyProperty(
            self.FRAMEPOSTFIX, b""
        )
        self.detectionProp = self.propertyOperator.createCustomReadOnlyProperty(
            self.DETECTIONPOSTFIX, b""
        )
        self.sendFrame = self.propertyOperator.createProperty(
            "Send-Frame", False, loadIfSaved=False
        )  # this is one of those properties that should always be opt-in and keep that after a restart

    def preprocessFrame(self, frame):
        """Optional method you can implement to add preprocessing to a frame"""
        return frame

    def runPeriodic(self):
        super().runPeriodic()
        ret, frame = self.cap.read()
        if ret:
            sendFrame = self.sendFrame.get()
            processedFrame = self.preprocessFrame(frame)
            processedResults = self.frameProcessor.processFrame(
                processedFrame,
                robotPosXCm=self.robotLocation[0] * 100,  # m to cm
                robotPosYCm=self.robotLocation[1] * 100,  # m to cm
                robotYawRad=self.robotLocation[2],
                drawBoxes=sendFrame,  # if you are sending frames, you likely want to see bounding boxes aswell
            )

            # add highest detection telemetry
            if processedResults:
                best_idx = max(
                    range(len(processedResults)), key=lambda i: processedResults[i][2]
                )
                best_result = processedResults[best_idx]
                x, y, z = best_result[1]
                self.propertyOperator.createReadOnlyProperty(
                    "BestResult.BestX", ""
                ).set(float(x))
                self.propertyOperator.createReadOnlyProperty(
                    "BestResult.BestY", ""
                ).set(float(y))
                self.propertyOperator.createReadOnlyProperty(
                    "BestResult.BestZ", ""
                ).set(float(z))

            timestamp = time.monotonic()

            detectionPacket = DetectionPacket.createPacket(
                processedResults, "Detection", timestamp
            )
            self.detectionProp.set(detectionPacket.to_bytes())

            # optionally send frame
            if sendFrame:
                # framePacket = FramePacket.createPacket(
                #     timestamp, "Frame", processedFrame
                # )
                self.xdashDebugger.send_frame(
                    key=self.sendFrame.getTable(),
                    timestamp=timestamp,
                    frame=processedFrame,
                )

            self.Sentinel.info("Processed frame!")

        else:
            self.detectionProp.set(b"")  # mark as empty

            self.Sentinel.error("Opencv Cap ret is false!")
            if self.cap.isOpened():
                self.cap.release()
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

    @staticmethod
    def getName():
        return "Inference_Agent_Process"

    @staticmethod
    def getDescription():
        return "Ingest_Camera_Run_Ai_Model"

    def getIntervalMs(self):
        return 1


def PartialFrameProcessingAgent(
    cameraPath, cameraIntrinsics, cameraExtrinsics, inferenceMode
):
    """Returns a partially completed frame processing agent. All you have to do is pass it into neo"""
    return partial(
        FrameProcessingAgent,
        cameraPath=cameraPath,
        cameraIntrinsics=cameraIntrinsics,
        cameraExtrinsics=cameraExtrinsics,
        inferenceMode=inferenceMode,
    )
