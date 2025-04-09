from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np
from ..Parameters.Intrinsics import CameraIntrinsics


class Capture(ABC):
    @abstractmethod
    def create(self) -> None:
        """Opens the capture, or throwing an exception if it cannot be opened"""
        pass

    @abstractmethod
    def getMainFrame(self) -> np.ndarray:
        """Returns the main capture frame"""
        pass

    @abstractmethod
    def getFps(self) -> int:
        """Returns fps of capture"""
        pass

    def getFrameShape(self) -> Tuple[int, ...]:
        """Returns the shape of the frame"""
        return self.getMainFrame().shape

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
        self.cameraIntrinsics: CameraIntrinsics = None  # must be set

    def setIntrinsics(self, cameraIntrinsics: CameraIntrinsics) -> None:
        """Set the camera intrinsics"""
        self.cameraIntrinsics = cameraIntrinsics

    def getIntrinsics(self) -> CameraIntrinsics:
        if self.cameraIntrinsics is None:
            raise ValueError(
                "Camera intrinsics is None!. Did you call Capture.create()?"
            )

        return self.cameraIntrinsics
