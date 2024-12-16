""" Local process to run on each orange pi """
import logging
import cv2
import socket
import time
from enum import Enum
from XTABLES.XTablesClient import XTablesClient
from coreinterface.FramePacket import FramePacket
from coreinterface.DetectionPacket import DetectionPacket
from tools.Constants import getCameraValues, CameraIntrinsics, CameraExtrinsics
from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools import calibration, NtUtils, CameraUtils

processName = "Central_Orange_Pi_Process"
logging.basicConfig(filename=f"logs/{processName}.log", level=logging.DEBUG)
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


classes = ["Robot", "Note"]

MAXITERTIMEMS = 50  # ms


def startProcess():
    name = getCameraName().name
    cameraIntrinsics, cameraExtrinsics, _ = getCameraValues(name)
    logger.info("Creating Frame Processor...")
    processor = LocalFrameProcessor(
        cameraIntrinsics=cameraIntrinsics,
        cameraExtrinsics=cameraExtrinsics,
        useRknn=True,
    )

    # frame undistortion maps
    mapx, mapy = calibration.createMapXYForUndistortion(
        cameraIntrinsics.getHres(), cameraIntrinsics.getVres()
    )

    logger.info("Starting process, device name:", name)
    xclient = XTablesClient(server_port=1735)
    cameraidx = CameraUtils.getCorrectCameraFeed()
    cap = cv2.VideoCapture(cameraidx)
    try:
        while cap.isOpened():
            stime = time.time()
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
                else:
                    logger.warning("Could not get robot pose!!")
                processedResults = processor.processFrame(
                    undistortedFrame,
                    True,
                    robotPosXCm=loc[0] * 100,
                    robotPosYCm=loc[1] * 100,
                    robotYawRad=loc[2],
                )  # processing as absolute if a robot pose is found
                detectionPacket = DetectionPacket.createPacket(
                    processedResults, name, timeStamp
                )
                detectionB64 = DetectionPacket.toBase64(detectionPacket)
            # sending network packets
            xclient.executePutString(name, detectionB64)
            etime = time.time()
            dMS = (etime - stime) * 1000
            if dMS > MAXITERTIMEMS:
                logger.warning(
                    f"Loop surpassing max iter time! Max:{MAXITERTIMEMS}ms | Loop time: {dMS}ms "
                )
            # cv2.imshow("frame", undistortedFrame)
            # if cv2.waitKey(1) & 0xFF == ord("q"):
            # break
    finally:
        logger.info("process finished, releasing camera object")
        cap.release()
        # cv2.destroyAllWindows()


if __name__ == "__main__":
    startProcess()
