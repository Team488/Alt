import cv2
import logging
from typing import List, Tuple, Optional


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
                if ret and frame.shape == expectedRes:
                    return idx
        return None
    except Exception as E:
        logging.error(f"Error when finding correct camera index! {E}")
        return None
