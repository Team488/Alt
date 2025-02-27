from typing import Union
import cv2
import numpy as np
from abstract.Capture import ConfigurableCapture
from tools.Constants import CameraIntrinsics


class ConfigurableCameraCapture(ConfigurableCapture):
    def __init__(self, cameraPath: Union[str, int], cameraIntrinsics: CameraIntrinsics):
        super().__init__(cameraIntrinsics)
        self.cap = cv2.VideoCapture(cameraPath)
        if not self.__testCapture(self.cap):
            raise BrokenPipeError(f"Failed to open video camera! {self.videoFilePath=}")
        # add configurable settings
        fourcc = cv2.VideoWriter_fourcc(*"MJPG")  # or 'XVID', 'MP4V'
        self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        CameraIntrinsics.setCapRes(self.cameraIntrinsics, self.cap)

    def __testCapture(self, cap: cv2.VideoCapture) -> bool:
        retTest = True
        if cap.isOpened():
            retTest, _ = cap.read()
        else:
            retTest = False
        return retTest

    def getColorFrame(self) -> np.ndarray:
        return self.cap.read()[1]

    def isOpen(self) -> bool:
        return self.cap.isOpened()

    def close(self) -> None:
        self.cap.release()
