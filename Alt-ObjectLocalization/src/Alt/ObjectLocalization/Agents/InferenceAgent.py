from typing import Any

from Alt.Core.Agents import BindableAgent
from Alt.Cameras.Agents.CameraUsingAgentBase import CameraUsingAgentBase
from Alt.Cameras.Captures import CaptureWIntrinsics

from ..Inference.ModelConfig import ModelConfig
from ..Inference.MultiInferencer import MultiInferencer


class InferenceAgent(CameraUsingAgentBase, BindableAgent):
    """Agent -> CameraUsingAgentBase -> InferenceAgent
    Adds inference capabilites to an agent, processing frames
    """
    @classmethod
    def bind(cls, 
        capture: CaptureWIntrinsics,
        modelConfig: ModelConfig,
        showFrames: bool = False,
    ):
        return cls.__getBindedAgent(capture=capture, modelConfig=modelConfig, showFrames=showFrames)

    def __init__(self, modelConfig : ModelConfig, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.modelConfig = modelConfig

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
