import os
import cv2
import time
from functools import partial

import numpy as np

# from JXTABLES.XDashDebugger import XDashDebugger

from Core.Agents.Abstract.TimestampRegulatedAgentBase import TimestampRegulatedAgentBase
from coreinterface.DetectionPacket import DetectionPacket
from tools.Constants import InferenceMode, CameraExtrinsics, CameraIntrinsics
from mapinternals.localFrameProcessor import LocalFrameProcessor
import Core


class ObjectLocalizingAgentBase(TimestampRegulatedAgentBase):
    """Agent -> (CameraUsingAgentBase, PositionLocalizingAgentBase) -> TimestampRegulatedAgentBase -> ObjectLocalizingAgentBase

    Adds inference and object localization capabilites to an agent, processing frames and sending detections
    NOTE: Requires extra arguments passed in somehow, for example using Functools partial or extending the class"""

    DETECTIONPOSTFIX = "Detections"

    def __init__(self, **kwargs):
        self.cameraIntrinsics = kwargs.get("cameraIntrinsics", None)
        self.cameraExtrinsics = kwargs.get("cameraExtrinsics", None)
        self.inferenceMode = kwargs.get("inferenceMode", None)
        super().__init__(**kwargs)

    def create(self):
        super().create()
        # self.xdashDebugger = XDashDebugger()
        self.Sentinel.info("Creating Frame Processor...")
        currentCoreINFName = self.xclient.getString(Core.COREMODELTABLE)
        currentCoreINFMode = InferenceMode.getFromName(currentCoreINFName, default=None)
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

        self.frameProcessor = LocalFrameProcessor(
            cameraIntrinsics=self.cameraIntrinsics,
            cameraExtrinsics=self.cameraExtrinsics,
            inferenceMode=self.inferenceMode,
        )
        self.detectionProp = self.propertyOperator.createCustomReadOnlyProperty(
            self.DETECTIONPOSTFIX, b""
        )

    def runPeriodic(self):
        super().runPeriodic()
        sendFrame = self.sendFrame.get()
        with self.timer.run("frame-processing"):
            processedResults = self.frameProcessor.processFrame(
                self.latestFrame,
                robotPosXCm=self.robotPose2dMRAD[0] * 100,  # m to cm
                robotPosYCm=self.robotPose2dMRAD[1] * 100,  # m to cm
                robotYawRad=self.robotPose2dMRAD[2],
                drawBoxes=sendFrame
                or self.showFrames,  # if you are sending frames, you likely want to see bounding boxes aswell
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
        self.detectionProp.set(detectionPacket.to_bytes())

        # optionally send frame

        self.Sentinel.info("Processed frame!")

    def getName(self):
        return "Object_Localizer"

    def getDescription(self):
        return "Inference_Then_Localize"

    def getIntervalMs(self):
        return 0


def ObjectLocalizingAgentPartial(
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
