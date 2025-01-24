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


processName = "Path_Test"
logger = logging.getLogger(processName)

# MJPEG stream URLs


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
clickpos = None


def clickCallback(event, x, y, flags, param):
    global clickpos
    if event == cv2.EVENT_LBUTTONDOWN:
        clickpos = (x, y)


cv2.setMouseCallback(title, clickCallback)


# Executor outside the with block

try:
    while running:
        if clickpos is not None:
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
                (pos[0] * 100, pos[1] * 100), clickpos, 0
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

        cv2.imshow(title, central.map.getRobotHeatMap())
        # Handle keyboard interrupt with cv2.waitKey()
        if cv2.waitKey(1) & 0xFF == ord("q"):
            running = False


except KeyboardInterrupt:
    print("Keyboard Interrupt detected, shutting down...")
    running = False

finally:
    # Gracefully shut down threads

    # Clean up resources
    cv2.destroyAllWindows()
    logging.info("Released all resources and closed windows.")
