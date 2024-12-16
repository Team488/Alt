import cv2
import logging


def getCorrectCameraFeed(idxOptions=[0, 1], expectedRes=(640, 640, 3)):
    try:
        for idx in idxOptions:
            cap = cv2.VideoCapture(idx)
            while cap.isOpened():
                ret, frame = cap.read()
                if ret and frame.shape == expectedRes:
                    return idx
    except Exception as E:
        logging.error(f"Error when finding correct camera index! {E}")
