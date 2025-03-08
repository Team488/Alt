from functools import partial
import cv2
from Core.Agents.Abstract import CameraUsingAgentBase
from abstract.Capture import Capture


class VideoWriterAgent(CameraUsingAgentBase):
    def __init__(self, capture: Capture, savePath: str, showFrames: bool):
        super().__init__(capture=capture, showFrames=showFrames)
        self.filePath = savePath

    def create(self):
        super().create()
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        self.writer = cv2.VideoWriter(
            self.filePath,
            fourcc,
            self.capture.getFps(),
            self.capture.getFrameShape()[:2][::-1],
        )

    def runPeriodic(self):
        super().runPeriodic()

        self.writer.write(self.latestFrameCOLOR)

    def getName(self):
        return "Video_Writer_Agent"

    def getDescription(self):
        return "Ingests-Camera-Writes-Frames-To-File"


def partialVideoWriterAgent(capture: Capture, savePath: str, showFrames: bool):
    return partial(
        VideoWriterAgent, capture=capture, savePath=savePath, showFrames=showFrames
    )
