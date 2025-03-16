import cv2
import logging
import numpy as np
from typing import List, Tuple, Optional, Union, Any


def getCorrectCameraFeed(
    idxOptions: List[int] = [0, 1], 
    expectedRes: Tuple[int, int, int] = (640, 640, 3)
) -> Optional[int]:
    """
    Find a camera with the specified resolution from the list of camera indices
    
    Args:
        idxOptions: List of camera indices to try
        expectedRes: Expected resolution of the camera feed as (height, width, channels)
        
    Returns:
        The index of the first camera that matches the expected resolution, or None if no match found
    """
    try:
        for idx in idxOptions:
            cap = cv2.VideoCapture(idx)
            while cap.isOpened():
                ret, frame = cap.read()
                # Check if frame is a numpy array with a shape attribute
                if ret and isinstance(frame, np.ndarray) and hasattr(frame, 'shape'):
                    frame_shape = tuple(frame.shape)
                    if frame_shape == expectedRes:
                        cap.release()
                        return idx
                break  # Only read one frame for testing
            cap.release()
        return None
    except Exception as E:
        logging.error(f"Error when finding correct camera index! {E}")
        return None
