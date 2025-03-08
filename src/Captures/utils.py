import time
import cv2


def flushCapture(cap: cv2.VideoCapture, flushTimeMs):
    flushS = flushTimeMs / 1000
    stime = time.time()
    while time.time() - stime < flushS:
        cap.grab()
