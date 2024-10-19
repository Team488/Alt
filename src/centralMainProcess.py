""" Process to run on orin """
import cv2
import numpy as np
from tools.Constants import CameraIdOffsets
from coreinterface.XTablesClient import XTablesClient
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.FramePacket import FramePacket
from mapinternals.CentralProcessor import CentralProcessor
from pathplanning.PathGenerator import PathGenerator
from tools.Constants import MapConstants


def getPackets(xtablesClient: XTablesClient):
    maxTimeout = 1000
    # keys = ("FRONTLEFT", "FRONTRIGHT", "REARLEFT", "REARRIGHT")
    keys = ["FRONTRIGHT"]
    detectionpackets = []
    framepackets = []
    for key in keys:
        print(f"Looking for key {key}")
        # detections
        rawB64 = xtablesClient.getString(key, TIMEOUT=maxTimeout)
        if rawB64 is not None and rawB64 and not rawB64.strip() == "null":
            dataPacket = DetectionPacket.fromBase64(rawB64.replace("\\u003d", "="))
            idOffset = CameraIdOffsets[dataPacket.message]
            detectionpackets.append(
                (DetectionPacket.toDetections(dataPacket), idOffset)
            )
        # frame
        rawB64 = xtablesClient.getString(key + "frame", TIMEOUT=maxTimeout)
        if rawB64 is not None and rawB64 and not rawB64.strip() == "null":
            dataPacket = FramePacket.fromBase64(rawB64.replace("\\u003d", "="))
            framepackets.append(dataPacket)

    return (detectionpackets, framepackets)


def mainLoop():
    MapBottomCorner = (MapConstants.fieldWidth, MapConstants.fieldHeight)
    client = XTablesClient()
    central = CentralProcessor.instance()
    pathGenerator = PathGenerator(central)
    pathName = "target_waypoints"
    currentPosition = MapBottomCorner / 2
    while True:
        (detPackets, framePackets) = getPackets(client)
        if detPackets:
            DetXY = detPackets[0][0][1][:2]  # x,y,z
            currentPosition = tuple(np.subtract(MapBottomCorner, DetXY))
            central.processFrameUpdate(detPackets, 0.06)
        for detPacket, framePacket in zip(detPackets, framePackets):
            print(detPacket)
            cv2.imshow(framePacket.message, FramePacket.getFrame(framePacket))

        path = pathGenerator.generate(currentPosition)

        if path == None:
            client.executePutString(pathName, [])
        else:
            out = []
            out = [{"x": waypoint[0], "y": waypoint[1]} for waypoint in path]
            client.executePutString(pathName, out)

        cv2.imshow("Robot Map", central.map.getHeatMaps()[0])
        cv2.imshow("Game object Map", central.map.getHeatMaps()[1])
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    client.shutdown()
    cv2.destroyAllWindows()


# print(time.time())
mainLoop()
