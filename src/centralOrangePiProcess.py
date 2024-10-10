""" Local process to run on each orange pi """
import numpy as np
import cv2
import socket
import time
from enum import Enum
from coreinterface.XTablesClient import XTablesClient
from coreinterface.FramePacket import FramePacket
from inference.rknnInferencer import rknnInferencer


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
    inf = rknnInferencer("assets/bestV5.rknn")
    print("Starting process, device name:", name)
    xclient = XTablesClient(server_ip="192.168.0.17", server_port=4880)
    cap = cv2.VideoCapture("assets/video12qual25clipped.mp4")
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"sending to key{name}")
            timeStamp = time.time()

            results = inf.getResults(frame)
            if results is not None:
                (boxes, classes, scores) = results
                for box, confidence, class_id in zip(boxes, classes, scores):
                    p1 = tuple(map(int, box[:2]))  # Convert to integer tuple
                    p2 = tuple(map(int, box[2:4]))  # Convert to integer tuple
                    cv2.rectangle(frame, p1, p2, (0, 255, 0), 2)

            dataPacket = FramePacket.createPacket(timeStamp, name, frame)
            b64 = FramePacket.toBase64(dataPacket)
            xclient.executePutString(name, b64)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    print("demo finished")
    xclient.shutdown()
    cap.release()
    cv2.destroyAllWindows()


startDemo()
