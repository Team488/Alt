""" Local process to run on each orange pi """
import numpy as np
import argparse
import cv2
import socket
import time
from enum import Enum
import XTablesClient
from coreinterface.FramePacket import FramePacket
from coreinterface.DetectionPacket import DetectionPacket
from tools.Constants import getCameraValues, CameraIntrinsics, CameraExtrinsics
from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools import calibration


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


def startDemo(args):
    # name = getCameraName().name
    name = "FRONTRIGHT"
    cameraIntrinsics, cameraExtrinsics, _ = getCameraValues(name)
    processor = LocalFrameProcessor(
        cameraIntrinsics=cameraIntrinsics,
        cameraExtrinsics=cameraExtrinsics,
        useRknn=False,
    )

    # frame undistortion maps
    mapx, mapy = calibration.createMapXYSForUndistortion(
        cameraIntrinsics.getHres(), cameraIntrinsics.getVres()
    )

    print("Starting process, device name:", name)
    # xclient = XTablesClient.XTablesClient(server_port=1735, useZeroMQ=True)
    cap = cv2.VideoCapture("assets/video12qual25clipped.mp4")
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            detectionB64 = ""
            if ret:
                print(f"sending to key{name}")
                timeStamp = time.time()

                undistortedFrame = calibration.undistortFrame(frame, mapx, mapy)
                processedResults = processor.processFrame(
                    undistortedFrame, True
                )  # processing as relative
                detectionPacket = DetectionPacket.createPacket(
                    processedResults, name, timeStamp
                )
                detectionB64 = DetectionPacket.toBase64(detectionPacket)
            # sending network packets
            if args.sendframe:
                dataPacket = FramePacket.createPacket(timeStamp, name, undistortedFrame)
                b64 = FramePacket.toBase64(dataPacket)
                # xclient.push_frame(name + "frame", b64)
            # xclient.executePutString(name, detectionB64)
            cv2.imshow("frame", undistortedFrame)
            if cv2.waitKey(1) & 0xFF == ord("q"):
                break
    finally:
        print("demo finished")
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Add an argument
    parser.add_argument("--sendframe", type=bool, required=False, default=False)
    # Parse the argument
    args = parser.parse_args()
    startDemo(args=args)
