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
    """Agent -> (CameraUsingAgentBase, PositionLocalizingAgentBase) -> TimestampRegulatedAgentBase -> ObjectLocalizingAgentBase

    Adds inference and object localization capabilites to an agent, processing frames and sending detections
    NOTE: Requires extra arguments passed in somehow, for example using Functools partial or extending the class"""

    DETECTIONPOSTFIX = "Detections"

    def __init__(self, **kwargs: Any) -> None:
        self.cameraExtrinsics: Optional[CameraExtrinsics] = kwargs.get(
            "cameraExtrinsics", None
        )
        self.inferenceMode: Optional[InferenceMode] = kwargs.get("inferenceMode", None)
        self.frameProcessor: Optional[LocalFrameProcessor] = None
        super().__init__(**kwargs)

    def create(self) -> None:
        super().create()
        self.cameraIntrinsics = self.capture.getIntrinsics()
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
        super().runPeriodic()

        if self.timer is None:
            raise ValueError("Timer not initialized")

        if self.frameProcessor is None:
            raise ValueError("Frame processor not initialized")

        if self.updateOp is None:
            raise ValueError("UpdateOperator not initialized")

        if self.Sentinel is None:
            raise ValueError("Logger not initialized")

        if (
            self.positionOffsetXM is None
            or self.positionOffsetYM is None
            or self.positionOffsetYAWDEG is None
        ):
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

    def getDescription(self) -> str:
        return "Inference_Then_Localize"

    def getIntervalMs(self) -> int:
        return 0


def ObjectLocalizingAgentPartial(
    capture: Union[depthCamera, ConfigurableCapture],
    cameraExtrinsics: CameraExtrinsics,
    inferenceMode: InferenceMode,
    showFrames: bool = False,
) -> Any:
    """Returns a partially completed frame processing agent. All you have to do is pass it into neo"""
    return partial(
        ObjectLocalizingAgentBase,
        capture=capture,
        cameraExtrinsics=cameraExtrinsics,
        inferenceMode=inferenceMode,
        showFrames=showFrames,
    )
