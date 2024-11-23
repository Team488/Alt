""" Process to run on orin """
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
from tools.Constants import MapConstants

central = CentralProcessor.instance()
client = XTablesClient(server_port=1735, useZeroMQ=True)

pathGenerator = PathGenerator(central)
pathName = "target_waypoints"
positionOffsetForCentralizing = 300


def handle_update(key, val):
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
        central.processFrameUpdate(
            [packet],
            0.06,
            positionOffset=(
                positionOffsetForCentralizing,
                positionOffsetForCentralizing,
                0,
            ),
        )
    # maps = central.map.getHeatMaps()
    target = central.map.getHighestGameObject()
    path = pathGenerator.generate(
        (positionOffsetForCentralizing, positionOffsetForCentralizing), target, 0
    )
    print(f"path: {path}")
    print(f"pathName: {pathName}")
    if path is None:
        client.executePutString(pathName, [{"x": 1, "y": 1}])
    else:
        out = [
            # remove the centralizing position offset and also turn cm to m
            {
                "x": (waypoint[0] - positionOffsetForCentralizing) / 100,
                "y": (waypoint[1] - positionOffsetForCentralizing) / 100,
            }
            for waypoint in path
        ]
        client.executePutString(pathName, out)
    # cv2.imshow("Robot Map", maps[1])
    # cv2.imshow("Game object Map", maps[0])
    # cv2.waitKey(1)


def mainLoop(args):
    global client

    try:
        client.subscribeForUpdates("REARRIGHT", consumer=handle_update)
        client.subscribeForUpdates("REARLEFT", consumer=handle_update)
        client.subscribeForUpdates("FRONTLEFT", consumer=handle_update)
        client.subscribeForUpdates("FRONTRIGHT", consumer=handle_update)

    except Exception as e:
        print(e)
    finally:
        print("Ending main process")
        cv2.destroyAllWindows()
        return


# print(time.time())
if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    parser = argparse.ArgumentParser()
    # Add an argument
    parser.add_argument("--show", type=bool, required=False, default=False)
    parser.add_argument("--fetchframe", type=bool, required=False, default=False)
    # Parse the argument
    args = parser.parse_args()
    mainLoop(args=args)
