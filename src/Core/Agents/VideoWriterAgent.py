from functools import partial
from typing import Any, Optional
import cv2
from Core.Agents.Abstract.CameraUsingAgentBase import CameraUsingAgentBase
from abstract.Capture import Capture


class VideoWriterAgent(CameraUsingAgentBase):
    def __init__(self, capture: Capture, savePath: str, showFrames: bool):
        super().__init__(capture=capture, showFrames=showFrames)
        self.filePath: str = savePath
        self.writer: Optional[cv2.VideoWriter] = None

    def create(self) -> None:
        super().create()
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
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

    def getName(self) -> str:
        return "Video_Writer_Agent"

    def getDescription(self) -> str:
        return "Ingests-Camera-Writes-Frames-To-File"


def partialVideoWriterAgent(capture: Capture, savePath: str, showFrames: bool = False) -> Any:
    """Returns a partially completed VideoWriterAgent that ingests camera frames and writes them to a file"""
    return partial(
        VideoWriterAgent, capture=capture, savePath=savePath, showFrames=showFrames
    )
