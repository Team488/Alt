""" Process to run on orin """
import time
import cv2
import argparse
import logging
import numpy as np
from tools.Constants import CameraIdOffsets
from XTABLES import XTablesClient
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.FramePacket import FramePacket
from mapinternals.CentralProcessor import CentralProcessor
from pathplanning.PathGenerator import PathGenerator
from tools.Constants import MapConstants,CameraExtrinsics,CameraIntrinsics

central = CentralProcessor.instance()
client = XTablesClient()

pathGenerator = PathGenerator(central)
pathName = "target_waypoints"
cams = (
    "FrontCam",
    "FrontLeftCam",
    "FrontRightCam",
    "BackLeftCam",
    "BackRightCam"
)



def handle_update(key, val):
    print(val)
    return
    global pathGenerator
    global pathName
    global client
    if not key or not val:
        return
    if val == "empty":
        central.processFrameUpdate([], 0.06)
        return
    dataPacket = DetectionPacket.fromBase64(val.replace("\\u003d", "="))
    idOffset = CameraIdOffsets[dataPacket.message]
    packet = (DetectionPacket.toDetections(dataPacket), idOffset)
    if packet and packet[0] and packet[0][0]:
        central.processFrameUpdate([packet], 0.06, positionOffset=(300, 300, 0))
    # maps = central.map.getHeatMaps()

    path = pathGenerator.generate((0, 0))
    print(f"path: {path}")
    print(f"pathName: {pathName}")
    if path is None:
        client.executePutString(pathName, [{"x": 1, "y": 1}])
    else:
        out = [
            {"x": (waypoint[0] - 300) / 100, "y": (waypoint[1] - 300) / 100}
            for waypoint in path
        ]
        client.executePutString(pathName, out)
    # cv2.imshow("Robot Map", maps[1])
    # cv2.imshow("Game object Map", maps[0])
    # cv2.waitKey(1)


def mainLoop():
    global client

    try:
        for cam in cams:
            client.subscribe_to_key(cam, consumer=handle_update)

        while True:
            time.sleep(1)
            
    except Exception as e:
        print(e)
    finally:
        print("Ending main process")
        cv2.destroyAllWindows()
        return


# print(time.time())
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    # Add an argument
    # Parse the argument
    mainLoop()
