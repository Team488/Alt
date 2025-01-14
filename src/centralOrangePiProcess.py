""" Local process to run on each orange pi """

import logging
import cv2
import socket
import time
from enum import Enum
from JXTABLES.XTablesClient import XTablesClient
from coreinterface.DetectionPacket import DetectionPacket
from tools.Constants import UnitMode, getCameraValues
from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools import calibration, NtUtils


processName = "Central_Orange_Pi_Process"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(processName)


class CameraName(Enum):
    REARRIGHT = "photonvisionrearright"
    REARLEFT = "photonvisionrearleft"
    FRONTRIGHT = "photonvisionfrontright"
    FRONTLEFT = "photonvisionfrontleft"


def getCameraName():
    name = socket.gethostname()
    logger.debug(f"Machine hostname {name}")
    return CameraName(name)



def startProcess():
    name = getCameraName().name
    cameraIntrinsics, cameraExtrinsics, _ = getCameraValues(name)
    logger.info("Creating Frame Processor...")
    processor = LocalFrameProcessor(
        cameraIntrinsics=cameraIntrinsics,
        cameraExtrinsics=cameraExtrinsics,
        unitMode=UnitMode.CM,
        useRknn=True,
    )

    # frame undistortion maps
    mapx, mapy = calibration.createMapXYForUndistortion(
        cameraIntrinsics.getHres(), cameraIntrinsics.getVres()
    )

    logger.info(f"Starting process, device name: {name}")
    xclient = XTablesClient()
    cap = cv2.VideoCapture(
        0
    )  # guaranteed as we are passing /dev/color_camera symlink to docker image as /dev/video0
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            defaultBytes = b""
            if ret:
                # print(f"sending to key{name}")
                timeStamp = time.time()

                undistortedFrame = calibration.undistortFrame(frame, mapx, mapy)
                undistortedFrame = frame
                posebytes = xclient.getBytes("robot_pose")  # ms
                loc = (0, 0, 0)  # x(m),y(m),rotation(rad)
                if posebytes:
                    loc = NtUtils.getPose2dFromBytes(posebytes)
                else:
                    logger.warning("Could not get robot pose!!")
                processedResults = processor.processFrame(
                    undistortedFrame,
                    robotPosXCm=loc[0] * 100, # m to cm
                    robotPosYCm=loc[1] * 100, # m to cm
                    robotYawRad=loc[2],
                )  # processing as absolute if a robot pose is found
                detectionPacket = DetectionPacket.createPacket(
                    processedResults, name, timeStamp
                )
                # sending network packets
                xclient.putBytes(name, detectionPacket.to_bytes())
            else:
                xclient.putBytes(name, defaultBytes)
            # cv2.imshow("frame", undistortedFrame)
            # if cv2.waitKey(1) & 0xFF == ord("q"):
            # break
    finally:
        logger.info("process finished, releasing camera object")
        cap.release()
        # cv2.destroyAllWindows()


if __name__ == "__main__":
    startProcess()
