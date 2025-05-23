from typing import Any, Optional
import cv2

from Alt.Core.Agents import BindableAgent
from .CameraUsingAgentBase import CameraUsingAgentBase
from ..Captures import Capture


class VideoWriterAgent(CameraUsingAgentBase, BindableAgent):
    @classmethod
    def bind(cls, capture: Capture, savePath: str, showFrames: bool):
        return cls._getBindedAgent(capture=capture, savePath=savePath, showFrames=showFrames)
    
    def __init__(self, capture: Capture, savePath: str, showFrames: bool, **kwargs):
        super().__init__(capture=capture, showFrames=showFrames, **kwargs)
        self.filePath: str = savePath
        self.writer: Optional[cv2.VideoWriter] = None

    def create(self) -> None:
        super().create()
        fourcc = cv2.VideoWriter_fourcc(*"mp4v") # type: ignore
        self.writer = cv2.VideoWriter(
            self.filePath,
            fourcc,
            self.capture.getFps(),
            self.capture.getFrameShape()[:2][::-1],
        )

    def runPeriodic(self) -> None:
        super().runPeriodic()

        if self.writer is None:
            raise ValueError("VideoWriter not initialized")

        if self.latestFrameMain is None:
            return

        self.writer.write(self.latestFrameMain)

    def onClose(self) -> None:
        super().onClose()
        if self.writer is not None:
            self.writer.release()

    def getDescription(self) -> str:
        return "Ingests-Camera-Writes-Frames-To-File"