""" Local process to run on each orange pi """
import logging
import cv2
import socket
import time
from enum import Enum
from coreinterface.FramePacket import FramePacket
from coreinterface.DetectionPacket import DetectionPacket
from tools.Constants import getCameraValues, CameraIntrinsics, CameraExtrinsics
from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools import calibration, NtUtils, CameraUtils

processName = "Central_Orange_Pi_Process"
logger = logging.getLogger(processName)
fh = logging.FileHandler(filename=f"logs/{processName}.log",mode="w")
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
 # create formatter and add it to the handlers
formatter = logging.Formatter('-->%(asctime)s - %(name)s:%(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)


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

MAXITERTIMEMS = 1000/15  # ms (15fps)


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
    cap = cv2.VideoCapture("assets/video12qual25clipped.mp4") # guaranteed as we are passing /dev/color_camera symlink to docker image as /dev/video0
    try:
        while cap.isOpened():
            stime = time.time()
            ret, frame = cap.read()
            if ret:

                undistortedFrame = calibration.undistortFrame(frame, mapx, mapy)
                processedResults = processor.processFrame(
                    undistortedFrame
                )  
                # print(processedResults)
            print("No results!")
            # sending network packets
            etime = time.time()
            dMS = (etime - stime) * 1000
            if dMS > MAXITERTIMEMS:
                logger.warning(
                    f"Loop surpassing max iter time! Max:{MAXITERTIMEMS}ms | Loop time: {dMS}ms "
                )
            else:
                time.sleep((MAXITERTIMEMS - dMS) / 1000)
    finally:
        logger.info("process finished, releasing camera object")
        cap.release()
        # cv2.destroyAllWindows()


if __name__ == "__main__":
    startProcess()
