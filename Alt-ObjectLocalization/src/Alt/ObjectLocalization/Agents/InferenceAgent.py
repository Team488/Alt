from functools import partial
from typing import Any

from Alt.Cameras.Agents.CameraUsingAgentBase import CameraUsingAgentBase
from Alt.Cameras.Captures import CaptureWIntrinsics

from ..Inference.ModelConfig import ModelConfig
from ..Inference.MultiInferencer import MultiInferencer


class InferenceAgent(CameraUsingAgentBase):
    """Agent -> CameraUsingAgentBase -> InferenceAgent
    Adds inference capabilites to an agent, processing frames
    NOTE: Requires extra arguments passed in somehow, for example using Functools partial or extending the class"""

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.modelConfig: ModelConfig = kwargs.get("modelConfig", None)

    def create(self) -> None:
        super().create()
        if self.Sentinel:
            self.Sentinel.info("Creating Frame Processor...")

        if self.modelConfig is None:
            raise ValueError("modelConfig not provided")

        self.inf = MultiInferencer(
            modelConfig=self.modelConfig,
        )

        self.confidence = self.propertyOperator.createProperty(
            "Confidence_Threshold", 0.7
        )
        self.drawBoxes = self.propertyOperator.createProperty("Draw_Boxes", self.showFrames) # if the camera using agent has show frames, then draw as default

    def runPeriodic(self) -> None:
        super().runPeriodic()

        with self.timer.run("inference"):
            self.results = self.inf.run(
                self.latestFrameMain, self.confidence.get(), self.drawBoxes.get()
            )

    def getDescription(self) -> str:
        return "Ingest_Camera_Run_Ai_Model"


def InferenceAgentPartial(
    capture: CaptureWIntrinsics,
    modelConfig: ModelConfig,
    showFrames: bool = False,
) -> Any:
    """Returns a partially completed frame processing agent. All you have to do is pass it into neo"""
    return partial(
        InferenceAgent,
        capture=capture,
        modelConfig=modelConfig,
        showFrames=showFrames,
    )
