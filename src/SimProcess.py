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
from tools.NtUtils import getPose2dFromBytes
from mapinternals.localFrameProcessor import LocalFrameProcessor
from mapinternals.CentralProcessor import CentralProcessor
from tools.Constants import (
    CameraExtrinsics,
    CameraIntrinsics,
    CameraIdOffsets,
    InferenceMode,
)
from tools.Units import UnitMode
from pathplanning.PathGenerator import PathGenerator


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
        inferenceMode=InferenceMode.ONNX2024,
        tryOCR=True,
        isSimulationMode=True,
    )
    for i in range(len(offsets))
]

central = CentralProcessor.instance()
pathGenerator = PathGenerator(central)

# Initialize NetworkTables
NetworkTables.initialize(server="127.0.0.1")
postable = NetworkTables.getTable("AdvantageKit/RealOutputs/PoseSubsystem")

xclient = XTablesClient()

# exit(0)


# Window setup for displaying the camera feed
title = "Simulation_Window"
camera_selector_name = "Camera Selection"
cv2.namedWindow(title)
cv2.createTrackbar(camera_selector_name, title, 0, 3, lambda x: None)
cv2.setTrackbarPos(camera_selector_name, title, 2)

cv2.createTrackbar("a", title, 0, 640, lambda x: None)
cv2.setTrackbarPos("a", title, 320)

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

    # Fetch NetworkTables data
    pos = (0, 0, 0)
    raw_data = postable.getEntry("RobotPose").get()
    if raw_data:
        pos = getPose2dFromBytes(raw_data)
        pos = (
            pos[0],
            pos[1],
            math.radians(pos[2]),
        )  # this one gives degrees by default
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
    cv2.imshow("Current Cam", frame)


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
        run_frameprocess(cv2.getTrackbarPos(camera_selector_name, title))

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

        pos = (0, 0, 0)
        raw_data = postable.getEntry("RobotPose").get()
        if raw_data:
            pos = getPose2dFromBytes(raw_data)
            pos = (
                pos[0],
                pos[1],
                math.radians(pos[2]),
            )  # this one gives degrees by default
        else:
            logger.warning("Cannot get robot location from network tables!")

        target = central.map.getHighestGameObjectT(0.2)
        path = pathGenerator.generate(
            (pos[0] * 100, pos[1] * 100), target[:2], 0
        )  # m to cm
        logger.debug(f"Generated Path: {path}")
        if path is None:
            logger.warning(f"No path found!")
            xclient.putCoordinates("target_waypoints", [])
        else:
            coordinates = []
            for waypoint in path:
                element = XTableValues_pb2.Coordinate(
                    x=waypoint[0] / 100, y=waypoint[1] / 100
                )
                coordinates.append(element)
            xclient.putCoordinates("target_waypoints", coordinates)

        print(central.map.getHighestGameObject())

        etime = time.time()
        dMS = (etime - stime) * 1000
        waittime = 0.001
        if dMS < MAINLOOPTIMEMS:
            waittime = int(MAINLOOPTIMEMS - dMS)
        else:
            logger.warning(
                f"Overran Loop! Time elapsed: {dMS}ms | Max loop time: {MAINLOOPTIMEMS}ms"
            )
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
