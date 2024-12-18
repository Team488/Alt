""" Process to run on orin """
import logging
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
from tools import NtUtils

processName = "Central_Orange_Pi_Process"
logger = logging.getLogger(processName)
fh = logging.FileHandler(filename=f"logs/{processName}.log",mode="w")
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
 # create formatter and add it to the handlers
formatter = logging.Formatter('-->%(asctime)s - %(name)s:%(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

central = CentralProcessor.instance()
client = XTablesClient(server_port=1735, useZeroMQ=True)

pathGenerator = PathGenerator(central)
pathName = "target_waypoints"
positionOffsetForCentralizing = 0
updateMap = {
    "FRONTLEFT": ([], 0, 0),
    "FRONTRIGHT": ([], 30, 0),
    "REARRIGHT": ([], 60, 0),
    "REARLEFT": ([], 90, 0),
}


def handle_update(key, val):
    global pathGenerator
    global pathName
    global updateMap

    idOffset = CameraIdOffsets[key]
    lastidx = updateMap[key][2]
    lastidx += 1

    if not key or not val:
        return
    if val == "empty":
        updateMap[key] = ([], idOffset, lastidx)
        return

    dataPacket = DetectionPacket.fromBase64(val.replace("\\u003d", "="))

    packet = (DetectionPacket.toDetections(dataPacket), idOffset, lastidx)
    if packet and packet[0] and packet[0][0]:
        updateMap[key] = packet


TIMEPERLOOPMS = 20  # ms


def mainLoop(args):
    global client
    global updateMap
    localUpdateMap = {"FRONTLEFT": 0, "FRONTRIGHT": 0, "REARRIGHT": 0, "REARLEFT": 0}
    keys = ["REARRIGHT", "REARLEFT", "FRONTLEFT", "FRONTRIGHT"]
    try:
        for key in keys:
            client.subscribeForUpdates(key, consumer=handle_update)

        while True:
            stime = time.time()
            accumulatedResults = []
            for key in keys:
                localidx = localUpdateMap[key]
                resultpacket = updateMap[key]
                res, packetidx = resultpacket[:2], resultpacket[2]
                if packetidx == localidx:
                    # no update same id
                    continue
                localUpdateMap[key] = packetidx
                accumulatedResults.append(res)

            central.processFrameUpdate(
                cameraResults=accumulatedResults, timeStepSeconds=TIMEPERLOOPMS / 1000
            )
            timeout = 20  # ms
            posebytes = client.getString("robot_pose", TIMEOUT=timeout)  # ms
            loc = (0, 0, 0)  # x(m),y(m),rotation(rad)
            if posebytes:
                loc = NtUtils.getPose2dFromBytes(posebytes)
            else:
                logger.warning(
                    "Unable to get robot position! using origin (0,0,0) instead"
                )
                logger.warning(f"Using timeout value : {timeout}")
            # maps = central.map.getHeatMaps()
            target = central.map.getHighestGameObject()
            if target[:2] == (0, 0):
                logger.warning("No suitable target found!")
                client.executePutString(pathName, [])
                etime = time.time()
                deltaMS = (etime - stime) * 1000
                if deltaMS < TIMEPERLOOPMS:
                    time.sleep((TIMEPERLOOPMS - deltaMS) / 1000)
                else:
                    logger.warning(
                        f"Could not complete loop within {TIMEPERLOOPMS}ms! (Even without calculating a path!!)\n Time elapsed on loop: {deltaMS}ms"
                    )
                continue

            path = pathGenerator.generate((loc[0], loc[1]), target, 0)

            logger.debug(f"Path Name: {pathName}")
            logger.debug(f"Generated Path: {path}")
            if path is None:
                logger.warning(f"No path found!")
                client.executePutString(pathName, [])
            else:
                out = [
                    # turn cm to m
                    {
                        "x": (waypoint[0]) / 100,
                        "y": (waypoint[1]) / 100,
                    }
                    for waypoint in path
                ]
                client.executePutString(pathName, out)

            etime = time.time()
            deltaMS = (etime - stime) * 1000
            if deltaMS < TIMEPERLOOPMS:
                time.sleep((TIMEPERLOOPMS - deltaMS) / 1000)
            else:
                logger.warning(
                    f"Could not complete loop within {TIMEPERLOOPMS}ms! | Time elapsed on loop: {deltaMS}ms"
                )
            # cv2.imshow("Robot Map", maps[1])
            # cv2.imshow("Game object Map", maps[0])
            # cv2.waitKey(1)

    except Exception as e:
        print(e)
    finally:
        logger.info("Ending main process")
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
