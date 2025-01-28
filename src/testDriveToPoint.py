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
from Core.Central import Central
from tools.Constants import (
    CameraExtrinsics,
    CameraIntrinsics,
    CameraIdOffsets,
    InferenceMode,
    MapConstants,
)
from tools.Units import UnitMode
from pathplanning.PathGenerator import PathGenerator


processName = "Path_Test"
logger = logging.getLogger(processName)


central = Central.instance()
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
clickpos = None
currentPath = None


def getAndSetPath(clickpos):
    global currentPath
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

    path = pathGenerator.generate(
        (MapConstants.fieldWidth.getCM() - pos[0] * 100, pos[1] * 100),
        clickpos,
        central.map.getRobotMap() > 0.1,
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


# Executor outside the with block

while True:
    frame = central.map.getRobotHeatMap().copy()
    if currentPath is not None:
        for point in currentPath:
            cv2.circle(frame, point, 2, (255, 255, 255), -1)

    cv2.imshow(title, frame)

    # Handle keyboard interrupt with cv2.waitKey()
    if cv2.waitKey(1) & 0xFF == ord("q"):
        break

cv2.destroyAllWindows()
logging.info("Released all resources and closed windows.")
