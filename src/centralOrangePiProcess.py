""" Local process to run on each orange pi """
import numpy as np
import cv2
import socket
import time
from enum import Enum
from coreinterface.XTablesClient import XTablesClient
from coreinterface.FramePacket import FramePacket


class CameraName(Enum):
    REARRIGHT = "photonvisionrearright"
    REARLEFT = "photonvisionrearleft"
    FRONTRIGHT = "photonvisionfrontright"
    FRONTLEFT = "photonvisionfrontleft"


def getCameraName():
    name = socket.gethostname()
    print(f"name:{name}")
    return CameraName(name)


def startDemo():
    name = getCameraName().name
    print("Starting process, device name:", name)
    xclient = XTablesClient()
    cap = cv2.VideoCapture("assets/video12qual25clipped.mp4")
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"sending to key{name}")
            timeStamp = time.time()
            dataPacket = FramePacket.createPacket(timeStamp, name, frame)
            b64 = FramePacket.toBase64(dataPacket)
            xclient.executePutString(name, b64)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    xclient.shutdown()
    cap.release()
    cv2.destroyAllWindows()


startDemo()
