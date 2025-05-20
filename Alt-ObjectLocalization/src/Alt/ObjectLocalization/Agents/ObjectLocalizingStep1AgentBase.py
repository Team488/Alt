import math
from typing import Optional, Any
import time

from Alt.Core import DEVICEHOSTNAME
from Alt.Core.Agents import BindableAgent
from Alt.Core.Agents.PositionLocalizingAgentBase import PositionLocalizingAgentBase
from Alt.Core.Units.Poses import Pose2d
from Alt.Cameras.Agents.CameraUsingAgentBase import CameraUsingAgentBase
from Alt.Cameras.Captures import CaptureWIntrinsics
from Alt.Cameras.Parameters.CameraExtrinsics import CameraExtrinsics

from ..Detections.DetectionPacket import DetectionPacket
from ..Inference.ModelConfig import ModelConfig
from ..Localization.PipelineStep1 import PipelineStep1
from ..Localization.LocalizationResult import DeviceLocalizationResult

class ObjectLocalizingStep1AgentBase(CameraUsingAgentBase, PositionLocalizingAgentBase, BindableAgent):
    """ Agent -> (CameraUsingAgentBase, PositionLocalizingAgentBase) -> ObjectLocalizingAgentBase
        Adds inference and object localization capabilites to an agent, processing frames and sending detections
    """
    DETECTIONPOSTFIX = "Detections"

    @classmethod
    def bind(
        cls,
        capture: CaptureWIntrinsics,
        cameraExtrinsics: CameraExtrinsics,
        modelConfig: ModelConfig,
        showFrames: bool = False,
    ):
        return cls.__getBindedAgent(capture=capture, cameraExtrinsics=cameraExtrinsics, modelConfig=modelConfig, showFrames=showFrames)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.cameraExtrinsics: Optional[CameraExtrinsics] = kwargs.get(
            "cameraExtrinsics", None
        )
        self.modelConfig: Optional[ModelConfig] = kwargs.get("modelConfig", None)
        self.localPipeline: Optional[PipelineStep1] = None

    def create(self) -> None:
        super().create()
        self.cameraIntrinsics = self.capture.getIntrinsics()

        self.localPipeline = PipelineStep1(
            self.modelConfig,
            cameraIntrinsics=self.cameraIntrinsics,
            cameraExtrinsics=self.cameraExtrinsics,
        )

    def runPeriodic(self) -> None:
        super().runPeriodic()

        offsetXCm = self.positionOffsetXM.get() * 100
        offsetYCm = self.positionOffsetYM.get() * 100
        offsetYawRAD = math.radians(self.positionOffsetYAWDEG.get())

        with self.timer.run("frame-processing"):
            localizedresults = self.localPipeline.runStep1(
                Pose2d(offsetXCm, offsetYCm, offsetYawRAD),
                self.latestFrameMain,
                self.latestFrameDEPTH,
                drawBoxes=self.showFrames,
                # if you are sending frames, you likely want to see bounding boxes aswell
            )

        timestampMs = time.time() * 1000
        deviceResult = DeviceLocalizationResult(localizedresults, DEVICEHOSTNAME)

        detectionPacket = DetectionPacket.createPacket(
            deviceResult, "Detection", timestampMs
        )
        self.updateOp.addGlobalUpdate(self.DETECTIONPOSTFIX, detectionPacket.to_bytes())

    def getDescription(self) -> str:
        return "Inference_Then_Localize(Step1)"
    
    def isRunning(self):
        return True
