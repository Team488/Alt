import numpy as np
from abstract.Capture import Capture
import cv2


class FileCapture(Capture):
    def __init__(self, videoFilePath: str) -> None:
        self.path = videoFilePath

    def create(self):
        self.cap = cv2.VideoCapture(self.path)
        if not self.__testCapture(self.cap):
            raise BrokenPipeError(f"Failed to open video camera! {self.path=}")

    def __testCapture(self, cap: cv2.VideoCapture) -> bool:
        retTest = True
        if cap.isOpened():
            retTest, _ = cap.read()
        else:
            retTest = False
        return retTest

    def getColorFrame(self) -> np.ndarray:
        return self.cap.read()[1]

    def getFps(self):
        return int(self.cap.get(cv2.CAP_PROP_FPS))

    def isOpen(self) -> bool:
        return self.cap.isOpened()

    def close(self) -> None:
        self.cap.release()


def startDemo(videoFilePath: str):
    cap = FileCapture(videoFilePath)
    cap.create()

    while cap.isOpen():
        frame = cap.getColorFrame()

        cv2.imshow("Video", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.close()
