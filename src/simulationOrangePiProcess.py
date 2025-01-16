""" Local process to run on each orange pi """

import logging
import math
import cv2
import socket
import time
from enum import Enum
from JXTABLES.XTablesClient import XTablesClient
from networktables import NetworkTables
from tools.NtUtils import getPose2dFromBytes
from coreinterface.DetectionPacket import DetectionPacket
from tools.Constants import UnitMode, getCameraValues
from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools import calibration, NtUtils


processName = "Central_Orange_Pi_Process"
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(processName)

NetworkTables.initialize(server="127.0.0.1")
postable = NetworkTables.getTable("SmartDashboard/VisionSystemSim-main/Sim Field")
table = NetworkTables.getTable("AdvantageKit/RealOutputs/Odometry")

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
    name = "FRONTRIGHT"
    FRUrl = f"http://localhost:3000/Robot_{name[:1] + name[1:].lower()}%20Camera?dummy=param.mjpg"
    cameraIntrinsics, cameraExtrinsics, _ = getCameraValues(name)
    logger.info("Creating Frame Processor...")
    processor = LocalFrameProcessor(
        cameraIntrinsics=cameraIntrinsics,
        cameraExtrinsics=cameraExtrinsics,
        unitMode=UnitMode.CM,
        useRknn=False,
    )

    logger.info(f"Starting process, device name: {name}")
    xclient = XTablesClient(ip="192.168.0.17",push_port=9999)
    cap = cv2.VideoCapture(
        "assets/video12qual25clipped.mp4"
    )  
    while cap.isOpened():
        try:
            ret, frame = cap.read()
            defaultBytes = b""
            if ret:
                # print(f"sending to key{name}")
                timeStamp = time.time()

                # posebytes = postable.getEntry("Robot").get()
                loc = (0, 0, 0)  # x(m),y(m),rotation(rad)
                # if posebytes:
                #     loc = (posebytes[0],posebytes[1],math.radians(posebytes[2]))
                # else:
                #     logger.warning("Could not get robot pose!!")
                processedResults = processor.processFrame(
                    frame,
                    robotPosXCm=loc[0] * 100, # m to cm
                    robotPosYCm=loc[1] * 100, # m to cm
                    robotYawRad=loc[2],
                    # drawBoxes=True
                )  # processing as absolute if a robot pose is found
                detectionPacket = DetectionPacket.createPacket(
                    processedResults, name, timeStamp
                )
                # sending network packets
                xclient.putBytes(name, detectionPacket.to_bytes())
            else:
                xclient.putBytes(name, defaultBytes)
            # cv2.imshow("frame", frame)
            # if cv2.waitKey(1) & 0xFF == ord("q"):
            #     break
        except Exception as e:
            print("ERRRORRR {e}") # use traceback
    logger.info("process finished, releasing camera object")
    cap.release()
    # cv2.destroyAllWindows()


if __name__ == "__main__":
    startProcess()
