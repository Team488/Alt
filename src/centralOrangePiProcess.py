""" Local process to run on each orange pi """

import logging
import cv2
import socket
import time
from enum import Enum
from JXTABLES.XTablesClient import XTablesClient
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.FramePacket import FramePacket
from tools.Constants import InferenceMode, getCameraValues
from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools import calibration, NtUtils, configLoader
from networktables import NetworkTables


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
    device_name = getCameraName().name
    cameraIntrinsics, cameraExtrinsics, _ = getCameraValues(device_name)
    logger.info("Creating Frame Processor...")
    processor = LocalFrameProcessor(
        cameraIntrinsics=cameraIntrinsics,
        cameraExtrinsics=cameraExtrinsics,
        inferenceMode=InferenceMode.RKNN2024
    )
    calib = configLoader.loadSavedCalibration()
    # frame undistortion maps
    mapx, mapy = calibration.createMapXYForUndistortion(
        cameraIntrinsics.getHres(), cameraIntrinsics.getVres(), calib
    )

    opiconfig = configLoader.loadOpiConfig() 
    pos_table : str = opiconfig["positionTable"]
    useXTablesForPos = opiconfig["useXTablesForPos"]
    showFrame = opiconfig["showFrame"]
    logger.info(f"Starting process, device name: {device_name}")
    xclient = XTablesClient(ip="192.168.0.17",push_port=9999, debug=True)
    xclient.add_client_version_property("ALT-VISION")
    if useXTablesForPos: 
        pos_entry = pos_table # xtables dosent really have tables like network tables
        client = xclient # use xtables for pos aswell
    else:
        NetworkTables.initialize(server="192.168.0.17")
        split_idx = pos_table.rfind("/")
        if split_idx == -1:
            logger.fatal(f"Invalid pos_table provided for network tables!: {pos_table}")
            exit(1)
        pos_entry = pos_table[split_idx+1:] # +1 to skip the "/"
        pos_table = pos_table[:split_idx]
        table = NetworkTables.getTable(pos_table)
        client = table
    cap = cv2.VideoCapture(
        "/dev/color_camera"
    )  # guaranteed as we are passing /dev/color_camera symlink to docker image
    try:
        while cap.isOpened():
            ret, frame = cap.read()
            defaultBytes = b""
            if ret:
                # print(f"sending to key{name}")
                timeStamp = time.time()

                undistortedFrame = calibration.undistortFrame(frame, mapx, mapy)
                loc = (0, 0, 0)  # default position x(m),y(m),rotation(rad)
                if useXTablesForPos:
                    posebytes = client.getBytes(pos_entry)
                else:
                    posebytes = client.getEntry(pos_entry).get()
                if posebytes:
                    loc = NtUtils.getPose2dFromBytes(posebytes)
                else:
                    logger.warning("Could not get robot pose!!")
                processedResults = processor.processFrame(
                    undistortedFrame,
                    robotPosXCm=loc[0] * 100, # m to cm
                    robotPosYCm=loc[1] * 100, # m to cm
                    robotYawRad=loc[2],
                    drawBoxes=showFrame
                )  # processing as absolute if a robot pose is found
                detectionPacket = DetectionPacket.createPacket(
                    processedResults, device_name, timeStamp
                )
                if showFrame:
                    framePacket = FramePacket.createPacket(timeStamp,device_name,undistortedFrame)
                    xclient.putBytes(device_name + "_frame", framePacket.to_bytes())

                # sending network packets
                xclient.putBytes(device_name, detectionPacket.to_bytes())
            else:
                logger.error("Opencv Cap ret is false!")
                xclient.putBytes(device_name, defaultBytes)
            # cv2.imshow("frame", undistortedFrame)
            # if cv2.waitKey(1) & 0xFF == ord("q"):
            # break
        else:
            logger.error("Opencv cap no longer opened!")
    except Exception as e:
        logger.fatal(f"Exception Occured!: {e}")
    
    finally:
        logger.info("process finished, releasing camera object")
        cap.release()
        # cv2.destroyAllWindows()


if __name__ == "__main__":
    startProcess()