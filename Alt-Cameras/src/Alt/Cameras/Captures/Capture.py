from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np
from ..Parameters.CameraIntrinsics import CameraIntrinsics
from ..Parameters.CameraConfig import CameraConfig


class Capture(ABC):
    def __init__(self, name : str):
        self.__name = f"{name}_{self.__class__.__name__}"
    
    def getName(self):
        return self.__name

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


class ConfigurableCapture:
    def setConfig(self, cameraConfig: CameraConfig) -> None:
        """Set the camera config"""
        self.cameraConfig = cameraConfig

    def getConfig(self) -> CameraConfig:
        if not hasattr(self, 'cameraConfig') or self.cameraConfig is None:
            raise ValueError(
                "Camera is missing cameraConfig!"
            )

        return self.cameraConfig
    

class CaptureWIntrinsics:
    def setIntrinsics(self, cameraIntrinsics: CameraIntrinsics) -> None:
        """Set the camera intrinsics"""
        self.cameraIntrinsics = cameraIntrinsics

    def getIntrinsics(self) -> CameraIntrinsics:
        if not hasattr(self, 'cameraIntrinsics') or self.cameraIntrinsics is None:
            raise ValueError(
                "Camera is missing cameraIntrinsics!"
            )

        return self.cameraIntrinsics
    
