import math
import struct
import time
import queue
import cv2
import logging
from JXTABLES.XTablesClient import XTablesClient
from JXTABLES import XTableValues_pb2
from concurrent.futures import ThreadPoolExecutor
from networktables import NetworkTables
import numpy as np
from tools.NtUtils import getPose2dFromBytes
from mapinternals.localFrameProcessor import LocalFrameProcessor
from mapinternals.CentralProcessor import CentralProcessor
from tools.Constants import (
    CameraExtrinsics,
    CameraIntrinsics,
    CameraIdOffsets,
    InferenceMode,
    MapConstants
)
from tools.Units import UnitMode
from pathplanning.PathGenerator import PathGenerator


processName = "Path_Test"
logger = logging.getLogger(processName)

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
        inferenceMode=InferenceMode.ULTRALYTICS2025,
        tryOCR=True,
        isSimulationMode=True
    )
    for i in range(len(offsets))
]

central = CentralProcessor.instance()
pathGenerator = PathGenerator(central)

# Initialize NetworkTables
NetworkTables.initialize(server="127.0.0.1")
postable = NetworkTables.getTable("AdvantageKit/RealOutputs/PoseSubsystem")

xclient = XTablesClient(ip="192.168.0.17", push_port=9999)

# exit(0)


# Window setup for displaying the camera feed
title = "Simulation_Window"
camera_selector_name = "Camera Selection"
cv2.namedWindow(title)
camera_selector_name = "Camera Selection"
cv2.createTrackbar(camera_selector_name,title,0,3, lambda x: None)
cv2.setTrackbarPos(camera_selector_name,title,2)
cv2.createTrackbar("TestRobotX",title,0,MapConstants.fieldWidth.getCM(), lambda x: None)
cv2.setTrackbarPos("TestRobotX",title,660)
cv2.createTrackbar("TestRobotY",title,0,MapConstants.fieldHeight.getCM(), lambda x: None)
cv2.setTrackbarPos("TestRobotY",title,535)
clickpos = None
currentPath = None

def getAndSetPath(clickpos):
    global currentPath
    pos = (0, 0, 0)
    raw_data = postable.getEntry("RobotPose").get()
    if raw_data:
        pos = getPose2dFromBytes(raw_data)
    else:
        logger.warning("Cannot get robot location from network tables!")

    path = pathGenerator.generate(
        (MapConstants.fieldWidth.getCM()-pos[0] * 100, pos[1] * 100), clickpos, central.map.getRobotMap() > 0.1
    )  # m to cm
    logger.debug(f"Generated Path: {path}")
    if path is None:
        logger.warning(f"No path found!")
        xclient.putCoordinates("target_waypoints", [])
    else:
        currentPath = path
        coordinates = []
        for waypoint in path:
            element = XTableValues_pb2.Coordinate(
                x=waypoint[0] / 100, y=waypoint[1] / 100
            )
            coordinates.append(element)
        xclient.putCoordinates("target_waypoints", coordinates)

def clickCallback(event, x, y, flags, param):
    global clickpos
    if event == cv2.EVENT_LBUTTONDOWN:
        getAndSetPath((x, y))


cv2.setMouseCallback(title, clickCallback)


updateMap = {
    "FRONTLEFT": ([], offsets[0], 0),
    "FRONTRIGHT": ([], offsets[1], 0),
    "REARRIGHT": ([], offsets[2], 0),
    "REARLEFT": ([], offsets[3], 0),
}


def run_frameprocess(imitatedProcIdx):
    cap = caps[imitatedProcIdx]
    imitatedProcName = names[imitatedProcIdx]
    idoffset = offsets[imitatedProcIdx]
    frameProcessor = frameProcessors[imitatedProcIdx]
    print(f"Starting sim thread idx: {imitatedProcIdx}")
    start_time = time.time()
    # Skip older frames in the buffer
    while cap.grab():
        if time.time() - start_time > 0.100:  # Timeout after 100ms
            logging.warning("Skipping buffer due to timeout.")
            break

    # Read a frame from the Front-Right camera stream
    ret, frame = cap.read()
    if not ret:
        logging.warning("Failed to retrieve a frame from stream.")
        exit(1)

    # put test robot pose
    x = cv2.getTrackbarPos("TestRobotX",title)
    y = cv2.getTrackbarPos("TestRobotY",title)
    postable.getEntry("TestRobotPose").setDoubleArray([x/100,y/100,0])

    highestRobot = central.map.getHighestRobot()
    postable.getEntry("VisionEstimatedRobotLocation").setDoubleArray([highestRobot[0]/100,highestRobot[1]/100,0])
    cv2.circle(frame,(int(MapConstants.fieldWidth.getCM()-highestRobot[0]),int(highestRobot[1])),5,(255),-1)



    # Fetch NetworkTables data
    pos = (0, 0, 0)
    raw_data = postable.getEntry("RobotPose").get()
    if raw_data:
        pos = getPose2dFromBytes(raw_data)
    else:
        logger.warning("Cannot get robot location from network tables!")

    print(f"{pos=}")
    # Process the frame
    res = frameProcessor.processFrame(
        frame,
        robotPosXCm=pos[0] * 100,  # Convert meters to cm
        robotPosYCm=pos[1] * 100,
        robotYawRad=pos[2],
        drawBoxes=True,
    )
    print(res)
    global updateMap
    lastidx = updateMap[imitatedProcName][2]
    lastidx += 1
    packet = (res, idoffset, lastidx)
    updateMap[imitatedProcName] = packet
    cv2.imshow("Current Cam",frame)



frame_queue = queue.Queue()

running = True
MAINLOOPTIMEMS = 100  # ms
localUpdateMap = {
    "FRONTLEFT": 0,
    "FRONTRIGHT": 0,
    "REARRIGHT": 0,
    "REARLEFT": 0,
}
        

while True:
    run_frameprocess(cv2.getTrackbarPos(camera_selector_name,title))
    stime = time.time()
    results = []
    for processName in names:
        localidx = localUpdateMap[processName]
        packet = updateMap[processName]
        # print(f"{packet=}")
        result, packetidx = packet[:2], packet[2]
        if localidx == packetidx:
            continue

        localUpdateMap[processName] = packetidx
        results.append(result)
        print(results)
    central.processFrameUpdate(results, 2)
    
    frame = central.map.getRobotHeatMap().copy()
    if currentPath is not None:
        for point in currentPath:
            cv2.circle(frame,point,2,(255,255,255),-1)

    cv2.imshow(title, frame)

    # Handle keyboard interrupt with cv2.waitKey()
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
logging.info("Released all resources and closed windows.")
