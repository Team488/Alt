import time
from typing import Optional
import cv2
import numpy as np


def flushCapture(cap: cv2.VideoCapture, flushTimeMs: int) -> None:
    """
    Flush the capture buffer by grabbing frames for the specified amount of time

    Args:
        cap: The OpenCV VideoCapture to flush
        flushTimeMs: Time in milliseconds to flush for
    """
    flushS = flushTimeMs / 1000
    stime = time.time()
    while time.time() - stime < flushS:
        cap.grab()
