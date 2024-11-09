""" Process to run on orin """
import cv2
import imutils
import argparse
import logging
import numpy as np
from tools.Constants import CameraIdOffsets
import XTablesClient
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.FramePacket import FramePacket
from mapinternals.CentralProcessor import CentralProcessor
from pathplanning.PathGenerator import PathGenerator
from tools.Constants import MapConstants

central = CentralProcessor.instance()


def handle_update(key, val):

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
            positionOffset=(central.map.width // 2, central.map.height // 2, 0),
        )
    maps = central.map.getHeatMaps()

    cv2.imshow("Robot Map", maps[1])
    cv2.imshow("Game object Map", maps[0])
    cv2.waitKey(1)


def mainLoop(args):
    MapBottomCorner = (MapConstants.fieldWidth.value, MapConstants.fieldHeight.value)
    client = XTablesClient.XTablesClient(server_port=1735, useZeroMQ=True)
    pathGenerator = PathGenerator(central)
    pathName = "target_waypoints"
    currentPosition = tuple(np.divide(MapBottomCorner, 2))

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
