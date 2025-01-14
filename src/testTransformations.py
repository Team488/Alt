import math
import struct
import time
import queue
import cv2
import logging
from concurrent.futures import ThreadPoolExecutor
from networktables import NetworkTables
import numpy as np
from tools.NtUtils import getPose2dFromBytes
from mapinternals.localFrameProcessor import LocalFrameProcessor
from mapinternals.CentralProcessor import CentralProcessor
from tools.Constants import CameraExtrinsics, CameraIntrinsics, CameraIdOffsets, UnitMode


processName = "Simulation_Process"
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

# MJPEG stream URLs
FRUrl = "http://localhost:3000/Robot_FrontRight%20Camera?dummy=param.mjpg"
FLUrl = "http://localhost:3000/Robot_FrontLeft%20Camera?dummy=param.mjpg"
RRUrl = "http://localhost:3000/Robot_RearRight%20Camera?dummy=param.mjpg"
RLUrl = "http://localhost:3000/Robot_RearLeft%20Camera?dummy=param.mjpg"

# Open the video streams

capFR = cv2.VideoCapture(FRUrl, cv2.CAP_FFMPEG)
capFL = cv2.VideoCapture(FLUrl, cv2.CAP_FFMPEG)
capRR = cv2.VideoCapture(RRUrl, cv2.CAP_FFMPEG)
capRL = cv2.VideoCapture(RLUrl, cv2.CAP_FFMPEG)

if (
    not capFR.isOpened()
    or not capFL.isOpened()
    or not capRR.isOpened()
    or not capRL.isOpened()
):
    logging.error(
        f"Failed to open streams! FR:{capFR.isOpened()}, FL:{capFL.isOpened()}, "
        f"RR:{capRR.isOpened()}, RL:{capRL.isOpened()}"
    )
    exit(1)

names = ["FRONTLEFT", "FRONTRIGHT", "REARRIGHT", "REARLEFT"]
caps = [capFR, capFL, capRR, capRL]

extrinsics = [
    CameraExtrinsics.FRONTRIGHT,
    CameraExtrinsics.FRONTLEFT,
    CameraExtrinsics.REARRIGHT,
    CameraExtrinsics.REARLEFT,
]
offsets = [
    CameraIdOffsets.FRONTRIGHT,
    CameraIdOffsets.FRONTLEFT,
    CameraIdOffsets.REARRIGHT,
    CameraIdOffsets.REARLEFT,
]

frameProcessors = [
    LocalFrameProcessor(
        cameraIntrinsics=CameraIntrinsics.SIMULATIONCOLOR,
        cameraExtrinsics=extrinsics[i],
        unitMode=UnitMode.CM,
        useRknn=False,
        tryOCR=True,
        isSimulationMode=True
    )
    for i in range(len(offsets))
]

central = CentralProcessor.instance()

# Initialize NetworkTables
NetworkTables.initialize(server="127.0.0.1")
postable = NetworkTables.getTable("SmartDashboard/Field")
table = NetworkTables.getTable("AdvantageKit/RealOutputs/Odometry")


# exit(0)


# Window setup for displaying the camera feed
title = "Simulation_Window"
camera_selector_name = "Camera Selection"
cv2.namedWindow(title)
cv2.createTrackbar(camera_selector_name,title,0,3, lambda x: None)
cv2.setTrackbarPos(camera_selector_name,title,2)

cv2.createTrackbar("a",title,0,640,lambda x : None)
cv2.setTrackbarPos("a",title,320)

updateMap = {
    "FRONTLEFT": ([], offsets[0], 0),
    "FRONTRIGHT": ([], offsets[1], 0),
    "REARRIGHT": ([], offsets[2], 0),
    "REARLEFT": ([], offsets[3], 0),
}


frame_queue = queue.Queue()

running = True
MAINLOOPTIMEMS = 100  # ms
localUpdateMap = {
    "FRONTLEFT": 0,
    "FRONTRIGHT": 0,
    "REARRIGHT": 0,
    "REARLEFT": 0,
}
# Executor outside the with block

try:
    while running:
        fakeData = [[3, np.array([429.48758498, 312.35349501,  30.60498969]), 1, False, np.ones(128)]]

        
        central.processFrameUpdate([fakeData], 0.2)
        coord = central.map.getHighestGameObjectT(0.1)
        if coord is not None:
            x, y, p = coord
            scaleFactor = 100  # cm to m
            table.getEntry("est/Target_Estimate").setDoubleArray(
                [x / scaleFactor, y / scaleFactor, 0, 0]
            )
        else:
            table.getEntry("est/Target_Estimate").setDoubleArray(
                [0,0, 0, 0]
            )

        print(central.map.getHighestGameObject())
        # logger.debug("Updated Target Estimate entry in NetworkTables.")

        etime = time.time()
        waittime = 0.001
        cv2.imshow(f"{title}_robots", central.map.getRobotHeatMap())
        cv2.imshow(f"{title}_notes", central.map.getGameObjectHeatMap())

        while not frame_queue.empty():
            print("In frame queue")
            name, frame = frame_queue.get()
            cv2.imshow(name, frame)
        # Handle keyboard interrupt with cv2.waitKey()
        if cv2.waitKey(1) & 0xFF == ord("q"):
            running = False

        time.sleep(waittime / 1000)

except KeyboardInterrupt:
    print("Keyboard Interrupt detected, shutting down...")
    running = False

finally:
    # Gracefully shut down threads

    # Clean up resources
    cv2.destroyAllWindows()
    if capFL.isOpened():
        capFL.release()
    if capFR.isOpened():
        capFR.release()
    if capRL.isOpened():
        capRL.release()
    if capRR.isOpened():
        capRR.release()
    logging.info("Released all resources and closed windows.")
