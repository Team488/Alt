""" Process to run on orin """

import cv2
import argparse
import logging
import time
import numpy as np
from tools.Constants import CameraIdOffsets
from JXTABLES.XTablesClient import XTablesClient
from JXTABLES import XTableValues_pb2
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.FramePacket import FramePacket
from mapinternals.CentralProcessor import CentralProcessor
from pathplanning.PathGenerator import PathGenerator
from tools import NtUtils

processName = "Central_Orange_Pi_Process"
logger = logging.getLogger(processName)
fh = logging.FileHandler(filename=f"{processName}.log", mode="w")
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
# create formatter and add it to the handlers
formatter = logging.Formatter("-->%(asctime)s - %(name)s:%(levelname)s - %(message)s")
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)
central = CentralProcessor.instance()
client = XTablesClient()
pathGenerator = PathGenerator(central)
pathName = "target_waypoints"
updateMap = {
    "FRONTLEFT": ([], 0, 0),
    "FRONTRIGHT": ([], 30, 0),
    "REARRIGHT": ([], 60, 0),
    "REARLEFT": ([], 90, 0),
}


def handle_update(ret):
    global updateMap
    key = ret.key
    val = ret.value
    idOffset = CameraIdOffsets[key]
    lastidx = updateMap[key][2]
    lastidx += 1
    if not key or not val:
        return
    if val == b"":
        updateMap[key] = ([], idOffset, lastidx)
        return
    det_packet = DetectionPacket.fromBytes(val)
    # print(f"{det_packet.timestamp=}")
    packet = (DetectionPacket.toDetections(det_packet), idOffset, lastidx)
    updateMap[key] = packet


TIMEPERLOOPMS = 50  # ms


def mainLoop():
    global client
    global updateMap
    localUpdateMap = {"FRONTLEFT": 0, "FRONTRIGHT": 0, "REARRIGHT": 0, "REARLEFT": 0}
    keys = ["REARRIGHT", "REARLEFT", "FRONTLEFT", "FRONTRIGHT"]
    try:
        for key in keys:
            client.subscribe(key, consumer=handle_update)
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
            posebytes = client.getBytes("robot_pose")  # ms
            loc = (0, 0, 0)  # x(m),y(m),rotation(rad)
            if posebytes:
                loc = NtUtils.getPose2dFromBytes(posebytes)
            else:
                logger.warning(
                    "Unable to get robot position! using origin (0,0,0) instead"
                )
            # maps = central.map.getHeatMaps()
            target = central.map.getHighestGameObject()
            if target[:2] == (0, 0):
                logger.warning("No suitable target found!")
                client.putCoordinates(pathName, [])
                etime = time.time()
                deltaMS = (etime - stime) * 1000
                if deltaMS < TIMEPERLOOPMS:
                    time.sleep((TIMEPERLOOPMS - deltaMS) / 1000)
                else:
                    logger.warning(
                        f"Could not complete loop within {TIMEPERLOOPMS}ms! (Even without calculating a path!!)\n Time elapsed on loop: {deltaMS}ms"
                    )
                continue
            path = pathGenerator.generate((loc[0]*100, loc[1]*100), target[:2], 0) # m to cm
            logger.debug(f"Path Name: {pathName}")
            logger.debug(f"Generated Path: {path}")
            if path is None:
                logger.warning(f"No path found!")
                client.putCoordinates(pathName, [])
            else:
                coordinates = []
                for waypoint in path:
                    element = XTableValues_pb2.Coordinate(x = waypoint[0]/100,y = waypoint[1]/100)
                    coordinates.append(element)
                client.putCoordinates(pathName, coordinates)
            etime = time.time()
            deltaMS = (etime - stime) * 1000
            if deltaMS < TIMEPERLOOPMS:
                time.sleep((TIMEPERLOOPMS - deltaMS) / 1000)
            else:
                logger.warning(
                    f"Could not complete loop within {TIMEPERLOOPMS}ms! | Time elapsed on loop: {deltaMS}ms"
                )
            # central.map.displayHeatMaps()
            # cv2.waitKey(1)
    except Exception as e:
        print(e)
    finally:
        logger.info("Ending main process")
        cv2.destroyAllWindows()
        return


# print(time.time())
if __name__ == "__main__":
    mainLoop()
