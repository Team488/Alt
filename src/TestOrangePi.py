import logging
import cv2
import socket
import time
from enum import Enum
from JXTABLES.XTablesClient import XTablesClient
from coreinterface.FramePacket import FramePacket

processName = "Orange_Pi_Test_Process"
logger = logging.getLogger(processName)
fh = logging.FileHandler(filename=f"logs/{processName}.log", mode="w")
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter("-->%(asctime)s - %(name)s:%(levelname)s - %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

cv2.ocl.setUseOpenCL(False)


class CameraName(Enum):
    REARRIGHT = "photonvisionrearright"
    REARLEFT = "photonvisionrearleft"
    FRONTRIGHT = "photonvisionfrontright"
    FRONTLEFT = "photonvisionfrontleft"


def getCameraName():
    name = socket.gethostname()
    logger.debug(f"Machine hostname {name}")
    return CameraName(name)


MAXITERTIMEMS = 1000 / 15  # ms (15fps)


def startProcess():
    name = getCameraName().name

    logger.info("Starting process, device name:", name)
    xclient = XTablesClient(ip="192.168.0.17")
    cap = cv2.VideoCapture(0)
    cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
    print("FourCC:", cap.get(cv2.CAP_PROP_FOURCC))

    try:
        while cap.isOpened():
            stime = time.time()
            ret, frame = cap.read()
            if ret:
                print(f"sending to key{name}")
                timeStamp = time.time()
                frame = FramePacket.createPacket(timeStamp, name, frame)
                xclient.putUnknownBytes(name, frame.to_bytes())
            etime = time.time()
            dMS = (etime - stime) * 1000
            if dMS > MAXITERTIMEMS:
                logger.warning(
                    f"Loop surpassing max iter time! Max:{MAXITERTIMEMS}ms | Loop time: {dMS}ms "
                )
            else:
                logger.info(f"Loop time: {dMS}ms")
            # cv2.imshow("frame", undistortedFrame)
            # if cv2.waitKey(1) & 0xFF == ord("q"):
            # break
    finally:
        logger.info("process finished, releasing camera object")
        cap.release()
        # cv2.destroyAllWindows()


if __name__ == "__main__":
    startProcess()
