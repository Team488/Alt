""" Local process to run on each orange pi """
import numpy as np
import cv2
import socket
import time
from enum import Enum
from coreinterface.XTablesClient import XTablesClient
from coreinterface.FramePacket import FramePacket
from coreinterface.DetectionPacket import DetectionPacket
from inference.rknnInferencer import rknnInferencer
from tools.Constants import getCameraValues, CameraIntrinsics, CameraExtrinsics
from mapinternals.localFrameProcessor import LocalFrameProcessor


class CameraName(Enum):
    REARRIGHT = "photonvisionrearright"
    REARLEFT = "photonvisionrearleft"
    FRONTRIGHT = "photonvisionfrontright"
    FRONTLEFT = "photonvisionfrontleft"


def getCameraName():
    name = socket.gethostname()
    print(f"name:{name}")
    return CameraName(name)


classes = ["Robot", "Note"]


def startDemo():
    name = getCameraName().name
    # cameraIntrinsics, cameraExtrinsics, _ = getCameraValues(name)
    cameraIntrinsics, cameraExtrinsics = (
        CameraIntrinsics.RANDOMWEBCAM,
        CameraExtrinsics.NONE,
    )
    processor = LocalFrameProcessor(
        cameraIntrinsics=cameraIntrinsics,
        cameraExtrinsics=cameraExtrinsics,
        useRknn=True,
    )
    print("Starting process, device name:", name)
    xclient = XTablesClient(server_ip="192.168.0.17", server_port=4880)
    cap = cv2.VideoCapture(0)
    # cap.set(cv2.CAP_PROP_POS_FRAMES, 1004)
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            print(f"sending to key{name}")
            timeStamp = time.time()

            processedResults = processor.processFrame(frame, True)
            detectionPacket = DetectionPacket.createPacket(
                processedResults, name, timeStamp
            )
            detectionB64 = DetectionPacket.toBase64(detectionPacket)
            xclient.executePutString(name, detectionB64)
            dataPacket = FramePacket.createPacket(timeStamp, name, frame)
            b64 = FramePacket.toBase64(dataPacket)
            xclient.executePutString(name + "frame", b64)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    print("demo finished")
    xclient.shutdown()
    cap.release()
    cv2.destroyAllWindows()


startDemo()
