import os
import cv2
import time
from functools import partial

import numpy as np

# from JXTABLES.XDashDebugger import XDashDebugger

from Core.Agents.Abstract.PositionLocalizingAgentBase import PositionLocalizingAgentBase
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.FramePacket import FramePacket
from tools.Constants import InferenceMode, CameraExtrinsics, CameraIntrinsics
from mapinternals.localFrameProcessor import LocalFrameProcessor


class ObjectLocalizingAgentBase(PositionLocalizingAgentBase):
    """Agent -> PositionLocalizingAgentBase -> ObjectLocalizingAgentBase

    Adds inference and object localization capabilites to an agent, processing frames and sending detections
    NOTE: Requires extra arguments passed in somehow, for example using Functools partial or extending the class"""

    DETECTIONPOSTFIX = "Detections"
    FRAMEPOSTFIX = "Frame"

    def __init__(
        self,
        cameraPath: str,
        cameraIntrinsics: CameraIntrinsics,
        cameraExtrinsics: CameraExtrinsics,
        inferenceMode: InferenceMode,
    ):
        self.cameraPath = cameraPath
        self.cameraIntrinsics = cameraIntrinsics
        self.cameraExtrinsics = cameraExtrinsics
        self.inferenceMode = inferenceMode

    def create(self):
        super().create()
        # self.xdashDebugger = XDashDebugger()
        self.cap = cv2.VideoCapture(self.cameraPath)
        retTest = True
        if self.cap.isOpened():
            retTest, _ = self.cap.read()

        if not self.cap.isOpened() or not retTest:
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
        self.checkSend = self.propertyOperator.createReadOnlyProperty(
            "Send-Frame-Value", False
        )
        self.exit = False

    def preprocessFrame(self, frame):
        """Optional method you can implement to add preprocessing to a frame"""
        return frame

    def runPeriodic(self):
        super().runPeriodic()

        with self.timer.run("cap_read"):
            ret, frame = self.cap.read()

        if ret:
            sendFrame = self.sendFrame.get()
            processedFrame = self.preprocessFrame(frame)
            with self.timer.run("frame-processing"):
                processedResults = self.frameProcessor.processFrame(
                    processedFrame,
                    robotPosXCm=self.robotPose2dMRAD[0] * 100,  # m to cm
                    robotPosYCm=self.robotPose2dMRAD[1] * 100,  # m to cm
                    robotYawRad=self.robotPose2dMRAD[2],
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

            timestampMs = time.time()*1000

            detectionPacket = DetectionPacket.createPacket(
                processedResults, "Detection", timestampMs
            )
            self.detectionProp.set(detectionPacket.to_bytes())

            # optionally send frame
            if sendFrame:
                self.checkSend.set(True)
                framePacket = FramePacket.createPacket(
                    timestampMs, "Frame", processedFrame
                )
                self.frameProp.set(framePacket.to_bytes())

                # self.xdashDebugger.send_frame(
                #     key=self.sendFrame.getTable(),
                #     timestamp=timestamp,
                #     frame=processedFrame,
                # )
            else:
                self.checkSend.set(False)

            self.Sentinel.info("Processed frame!")

        else:
            self.detectionProp.set(b"")  # mark as empty

            self.Sentinel.error("Opencv Cap ret is false!")
            if self.cap.isOpened():
                self.cap.release()

            self.exit = True
            # will close cap

    def onClose(self):
        super().onClose()
        if self.cap.isOpened():
            self.cap.release()

    def isRunning(self):
        if self.exit:
            return False

        if not self.cap.isOpened():
            self.Sentinel.fatal("Camera cant be opened!")
            return False
        return True

    def forceShutdown(self):
        super().forceShutdown()
        self.cap.release()

    def getName(self):
        return "Object_Localizer"

    def getDescription(self):
        return "Inference_Then_Localize"

    def getIntervalMs(self):
        return 0


def PartialObjectLocalizingAgent(
    cameraPath, cameraIntrinsics, cameraExtrinsics, inferenceMode
):
    """Returns a partially completed frame processing agent. All you have to do is pass it into neo"""
    return partial(
        ObjectLocalizingAgentBase,
        cameraPath=cameraPath,
        cameraIntrinsics=cameraIntrinsics,
        cameraExtrinsics=cameraExtrinsics,
        inferenceMode=inferenceMode,
    )
