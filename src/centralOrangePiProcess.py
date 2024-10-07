""" Local process to run on each orange pi """
import numpy as np
import cv2
import socket
import time
from enum import Enum
from coreinterface.XTablesClient import XTablesClient
from coreinterface.DataPacket import DataPacket


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
    print("Starting process, device name:",name)
    xclient = XTablesClient()
    cap = cv2.VideoCapture("assets/video12qual25clipped.mp4")
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            timeStamp = time.time()
            dataPacket = DataPacket(timeStamp, name, frame)
            xclient.executePutString(name, dataPacket)

        time.sleep(0.05)  # remove this
    cap.release()
    cv2.destroyAllWindows()


startDemo()
