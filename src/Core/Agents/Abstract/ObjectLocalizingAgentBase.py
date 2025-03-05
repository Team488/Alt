import math
import os
from typing import Union
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
    """Agent -> (CameraUsingAgentBase, PositionLocalizingAgentBase) -> TimestampRegulatedAgentBase -> ObjectLocalizingAgentBase

    Adds inference and object localization capabilites to an agent, processing frames and sending detections
    NOTE: Requires extra arguments passed in somehow, for example using Functools partial or extending the class"""

    DETECTIONPOSTFIX = "Detections"

    def __init__(self, **kwargs) -> None:
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
            depthMode=self.depthEnabled,
        )

    def runPeriodic(self) -> None:
        super().runPeriodic()
        sendFrame = self.sendFrame
        offsetXCm = self.positionOffsetXM.get() * 100
        offsetYCm = self.positionOffsetYM.get() * 100
        offsetYawRAD = math.radians(self.positionOffsetYAWDEG.get())
        with self.timer.run("frame-processing"):
            processedResults = self.frameProcessor.processFrame(
                self.latestFrameCOLOR,
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
        return "Object_Localizer"

    def getDescription(self) -> str:
        return "Inference_Then_Localize"

    def getIntervalMs(self) -> int:
        return 0


def ObjectLocalizingAgentPartial(
    capture: Union[depthCamera, ConfigurableCapture],
    cameraExtrinsics: CameraExtrinsics,
    inferenceMode: InferenceMode,
    showFrames: bool = False,
):
    """Returns a partially completed frame processing agent. All you have to do is pass it into neo"""
    return partial(
        ObjectLocalizingAgentBase,
        capture=capture,
        cameraIntrinsics=capture.getIntrinsics(),
        cameraExtrinsics=cameraExtrinsics,
        inferenceMode=inferenceMode,
        showFrames=showFrames,
    )
