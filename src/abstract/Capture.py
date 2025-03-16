from abc import ABC, abstractmethod
from typing import Tuple

import numpy as np

from tools.Constants import CameraIntrinsics


class Capture(ABC):
    @abstractmethod
    def create(self) -> None:
        """Opens the capture, or throwing an exception if it cannot be opened"""
        pass

    @abstractmethod
    def getColorFrame(self) -> np.ndarray:
        """Returns a color frame"""
        pass

    @abstractmethod
    def getFps(self) -> int:
        """Returns fps of capture"""
        pass

    def getFrameShape(self) -> Tuple[int, ...]:
        """Returns the shape of the frame"""
        return self.getColorFrame().shape

    @abstractmethod
    def isOpen(self) -> bool:
        """Returns a boolean representing if the capture is open"""
        pass

    @abstractmethod
    def close(self) -> None:
        """Close the capture"""
        pass


class ConfigurableCapture(Capture):
    def __init__(self) -> None:
        super().__init__()
        self.cameraIntrinsics: CameraIntrinsics = CameraIntrinsics()

    def setIntrinsics(self, cameraIntrinsics: CameraIntrinsics) -> None:
        """Set the camera intrinsics"""
        self.cameraIntrinsics = cameraIntrinsics

    def getIntrinsics(self) -> CameraIntrinsics:
        """Get the camera intrinsics"""
        return self.cameraIntrinsics
