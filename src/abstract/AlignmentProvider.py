"""
AlignmentProvider Module - Abstract interface for alignment detection and calculation.

This module defines the base interface for alignment providers, which are components
that analyze camera frames to determine positional alignment relative to targets
in the environment. Alignment providers calculate left/right offsets from the center
of the frame, which can be used for visual servoing, positioning, and navigation.

Different implementations may use color-based detection, feature recognition,
or other computer vision techniques to determine alignment.
"""

from abc import ABC, abstractmethod

import numpy as np

from Core import PropertyOperator

class AlignmentProvider(ABC):
    """
    Abstract base class for alignment detection and calculation.
    
    Alignment providers analyze camera frames to determine positional alignment
    relative to targets in the environment. They calculate left/right offsets
    from the center of the frame, which can be used for visual servoing,
    positioning, and navigation.
    
    All alignment providers assume centering on the camera and provide offset values
    relative to the center of the frame. Some implementations may require color
    frames (RGB/BGR), while others can work with grayscale images.
    """
    @abstractmethod
    def __init__(self) -> None:
        """
        Initialize the alignment provider.
        
        Subclasses should perform any necessary initialization in this method,
        such as loading calibration data, setting up parameters, or initializing
        internal state.
        """
        pass

    @abstractmethod
    def isColorBased() -> bool:
        """
        Check if this alignment provider requires color frames.
        
        Returns:
            bool: True if the provider requires color frames, False if it works with grayscale
            
        Note:
            This method should be implemented as a class method or static method,
            but the abstract base class defines it as an instance method to maintain
            a consistent interface.
        """
        pass

    @abstractmethod
    def align(self, frame: np.ndarray, showFrames: bool) -> tuple[int, int]:
        """
        Calculate alignment offsets based on the input frame.
        
        This method analyzes the input frame to determine left/right offsets from the
        center of the frame. If a side is not visible, it will return -1 for that side.
        
        Args:
            frame: The input frame to analyze (color or grayscale, depending on isColorBased())
            showFrames: Whether to display visualization frames for debugging
            
        Returns:
            tuple[int, int]: A tuple of (left, right) pixel offsets from the center
                             -1 indicates that a side is not visible
        """
        pass
      
    def shutDown(self) -> None:
        """
        Perform cleanup when the alignment provider is no longer needed.
        
        This method releases any resources held by the alignment provider.
        The default implementation does nothing. Subclasses should override
        this method if they need to perform cleanup operations.
        """
        pass

    def checkFrame(self, frame: np.ndarray) -> bool:
        """
        Check if the given frame is valid for this alignment provider.
        
        This helper method verifies that the frame has the correct number of
        channels (color or grayscale) for the alignment provider.
        
        Args:
            frame: The frame to check
            
        Returns:
            bool: True if the frame is valid for this provider, False otherwise
        """
        numChannels = frame.shape[2]

        isColor = numChannels > 1
        isAlignmentColor = self.isColorBased()

        return isColor == isAlignmentColor

        

    



