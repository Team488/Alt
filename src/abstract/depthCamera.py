"""
DepthCamera Module - Abstract interface for depth-sensing cameras.

This module defines the base interface for depth cameras, which are capture
devices that provide both color (RGB) and depth information. The depthCamera
class extends the ConfigurableCapture interface to add depth-specific
functionality, such as retrieving aligned depth and color frames.

Depth cameras are essential for 3D perception tasks like object distance
estimation, 3D reconstruction, and spatial mapping.
"""

import numpy as np
from abc import abstractmethod
from typing import Tuple

from abstract.Capture import ConfigurableCapture


class depthCamera(ConfigurableCapture):
    """
    Abstract base class for depth-sensing cameras.
    
    This class extends ConfigurableCapture to add depth-specific functionality
    for cameras that capture both color and depth information. It provides
    methods to retrieve aligned depth and color frames, where each pixel in the
    color frame corresponds to the same point in 3D space as the corresponding
    pixel in the depth frame.
    
    Implementations of this class typically interface with specific depth camera
    hardware, such as Intel RealSense, Microsoft Kinect, or OAK-D cameras.
    """
    
    @abstractmethod
    def getDepthAndColorFrame(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get aligned depth and color frames with one-to-one pixel mapping.
        
        This method returns a pair of frames (depth and color) that are spatially
        aligned, meaning that each pixel in the color frame corresponds to the
        same physical point as the corresponding pixel in the depth frame.
        
        Returns:
            Tuple[np.ndarray, np.ndarray]: A tuple containing:
                - Depth frame as a 2D numpy array (height, width)
                - Color frame as a 3D numpy array (height, width, channels)
                
        Raises:
            Exception: If frames cannot be captured or aligned
        """
        pass

    @abstractmethod
    def getDepthFrame(self) -> np.ndarray:
        """
        Get only the depth frame (already aligned to the color frame).
        
        This method returns just the depth frame, already aligned to the
        color frame's viewpoint. The depth values typically represent
        distance in millimeters from the camera.
        
        Returns:
            np.ndarray: The depth frame as a 2D numpy array (height, width)
            
        Raises:
            Exception: If the depth frame cannot be captured
        """
        pass
