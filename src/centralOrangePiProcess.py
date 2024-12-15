""" Local process to run on each orange pi """
import cv2
import socket
import time
from enum import Enum
from XTABLES.XTablesClient import XTablesClient
from coreinterface.FramePacket import FramePacket
from coreinterface.DetectionPacket import DetectionPacket
from tools.Constants import getCameraValues, CameraIntrinsics, CameraExtrinsics
from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools import calibration, NtUtils


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


def startProcess():
    name = getCameraName().name
    cameraIntrinsics, cameraExtrinsics, _ = getCameraValues(name)
    processor = LocalFrameProcessor(
        cameraIntrinsics=cameraIntrinsics,
        cameraExtrinsics=cameraExtrinsics,
        useRknn=True,
    )

    # frame undistortion maps
    mapx, mapy = calibration.createMapXYForUndistortion(
        cameraIntrinsics.getHres(), cameraIntrinsics.getVres()
    )

    print("Starting process, device name:", name)
    xclient = XTablesClient(server_port=1735)
    cap = cv2.VideoCapture(0)
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            detectionB64 = ""
            if ret:
                # print(f"sending to key{name}")
                timeStamp = time.time()

                undistortedFrame = calibration.undistortFrame(frame, mapx, mapy)
                posebytes = xclient.getString("robot_pose", TIMEOUT=20)  # ms
                loc = (0, 0, 0)  # x(m),y(m),rotation(rad)
                if posebytes:
                    loc = NtUtils.getPose2dFromBytes(posebytes)
                processedResults = processor.processFrame(
                    undistortedFrame,
                    True,
                    robotPosXCm=loc[0] * 100,
                    robotPosYCm=loc[1] * 100,
                    robotYawRad=loc[2],
                )  # processing as absolute if a location is found
                detectionPacket = DetectionPacket.createPacket(
                    processedResults, name, timeStamp
                )
                detectionB64 = DetectionPacket.toBase64(detectionPacket)
            # sending network packets
            xclient.executePutString(name, detectionB64)
            # cv2.imshow("frame", undistortedFrame)
            # if cv2.waitKey(1) & 0xFF == ord("q"):
            # break
    finally:
        print("process finished")
        cap.release()
        # cv2.destroyAllWindows()


if __name__ == "__main__":
    startProcess()
