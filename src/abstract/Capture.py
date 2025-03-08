from abc import ABC, abstractmethod
import numpy as np

from tools.Constants import CameraIntrinsics


class Capture(ABC):
    @abstractmethod
    def create(self):
        """Opens the capture, or throwing an exception if it cannot be opened"""

    @abstractmethod
    def getColorFrame(self) -> np.ndarray:
        """Returns a color frame"""
        pass

    @abstractmethod
    def getFps(self) -> int:
        """Returns fps of capture"""
        pass

    def getFrameShape(self):
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
    def setIntrinsics(self, cameraIntrinsics: CameraIntrinsics):
        self.cameraIntrinsics = cameraIntrinsics

    def getIntrinsics(self) -> CameraIntrinsics:
        return self.cameraIntrinsics
