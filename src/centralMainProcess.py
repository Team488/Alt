""" Process to run on orin """
import cv2
from tools.Constants import CameraExtrinsics, CameraIntrinsics, CameraIdOffsets
from tools.Constants import getCameraValues
from mapinternals.localFrameProcessor import LocalFrameProcessor
from coreinterface.XTablesClient import XTablesClient
from coreinterface.DataPacket import DataPacket


def getPackets(xtablesClient: XTablesClient):
    maxTimeout = 100
    keys = ("FRONTLEFT", "FRONTRIGHT", "REARLEFT", "REARRIGHT")
    packets = []
    for key in keys:
        rawJson = xtablesClient.getString(key, TIMEOUT=maxTimeout)
        dataPacket = DataPacket.decode(rawJson)
        packets.append(dataPacket)

    return packets


def mainLoop():
    client = XTablesClient()
    # frameProcessors = [LocalFrameProcessor(CameraIntrinsics.OV9782COLOR,CameraExtrinsics.)]

    # frameProcessor =
    while True:
        packets: list[DataPacket] = getPackets()
        for packet in packets:
            cv2.imshow(packet.message, packet.frame)
