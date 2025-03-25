"""
Capture Module - Abstract interface for camera and video captures.

This module defines the base interfaces for all capture sources in the system,
including cameras, video files, and simulated inputs. The Capture abstract base
class defines the core functionality that all capture sources must implement,
while the ConfigurableCapture subclass adds support for camera intrinsics.

The Capture interfaces provide a unified way to acquire frames from different 
sources, enabling the system to work with various camera types and recorded 
videos interchangeably.
"""

from abc import ABC, abstractmethod
from typing import Tuple

import numpy as np

from tools.Constants import CameraIntrinsics


class Capture(ABC):
    """
    Abstract base class for all camera and video capture sources.
    
    This class defines the common interface that all capture sources must implement,
    providing methods to open, read frames from, and close the capture. Captures
    can represent physical cameras, video files, network streams, or simulated
    inputs.
    
    All capture sources must implement at minimum the create(), getMainFrame(),
    getFps(), isOpen(), and close() methods.
    """
    
    @abstractmethod
    def create(self) -> None:
        """
        Initialize and open the capture source.
        
        This method should perform all necessary initialization to prepare 
        the capture for use, such as opening a camera or video file.
        
        Raises:
            Exception: If the capture cannot be opened or initialized
        """
        pass

    @abstractmethod
    def getMainFrame(self) -> np.ndarray:
        """
        Get the next frame from the capture source.
        
        Returns:
            np.ndarray: The captured frame as a NumPy array in BGR format
            
        Raises:
            Exception: If the frame cannot be read
        """
        pass

    @abstractmethod
    def getFps(self) -> int:
        """
        Get the frames per second of the capture source.
        
        Returns:
            int: The frame rate of the capture in frames per second
        """
        pass

    def getFrameShape(self) -> Tuple[int, ...]:
        """
        Get the dimensions of frames from this capture source.
        
        This method provides the shape of the frames produced by the capture,
        typically as (height, width, channels).
        
        Returns:
            Tuple[int, ...]: The shape of the frames (height, width, channels)
        """
        return self.getMainFrame().shape

    @abstractmethod
    def isOpen(self) -> bool:
        """
        Check if the capture source is currently open.
        
        Returns:
            bool: True if the capture is open and operational, False otherwise
        """
        pass

    @abstractmethod
    def close(self) -> None:
        """
        Close the capture source and release any resources.
        
        This method should clean up any resources used by the capture,
        such as closing file handles or releasing camera devices.
        """
        pass


class ConfigurableCapture(Capture):
    """
    Extended capture class that supports camera intrinsics configuration.
    
    This class extends the base Capture interface to add support for camera
    intrinsics, which include parameters like focal length, principal point,
    and other camera calibration data. It's used for captures where geometric
    calculations like depth estimation or 3D reconstruction are needed.
    
    Attributes:
        cameraIntrinsics (CameraIntrinsics): The intrinsic parameters of the camera
    """
    def __init__(self) -> None:
        """
        Initialize the configurable capture with default camera intrinsics.
        """
        super().__init__()
        self.cameraIntrinsics: CameraIntrinsics = CameraIntrinsics()

    def setIntrinsics(self, cameraIntrinsics: CameraIntrinsics) -> None:
        """
        Set the camera intrinsic parameters.
        
        Args:
            cameraIntrinsics: The camera intrinsics to use for this capture
        """
        self.cameraIntrinsics = cameraIntrinsics

    def getIntrinsics(self) -> CameraIntrinsics:
        """
        Get the current camera intrinsic parameters.
        
        Returns:
            CameraIntrinsics: The current camera intrinsics
        """
        return self.cameraIntrinsics
