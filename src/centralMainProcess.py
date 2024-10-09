""" Process to run on orin """
import cv2
from tools.Constants import CameraExtrinsics, CameraIntrinsics, CameraIdOffsets
from coreinterface.XTablesClient import XTablesClient
from coreinterface.FramePacket import FramePacket
import time


def getPackets(xtablesClient: XTablesClient):
    maxTimeout = 10000
    # keys = ("FRONTLEFT", "FRONTRIGHT", "REARLEFT", "REARRIGHT")
    keys = ["FRONTRIGHT"]
    packets = []
    for key in keys:
        print(f"Looking for key {key}")
        rawJson = xtablesClient.getString(key, TIMEOUT=maxTimeout)
        if rawJson is not None and not rawJson.strip() == "null":
            dataPacket = FramePacket.fromBase64(rawJson)
            packets.append(dataPacket)

    return packets


def mainLoop():
    client = XTablesClient()
    # frameProcessors = [LocalFrameProcessor(CameraIntrinsics.OV9782COLOR,CameraExtrinsics.)]

    # frameProcessor =
    while True:
        packets: list[FramePacket] = getPackets(client)
        for packet in packets:
            frame = FramePacket.getFrame(packet)
            cv2.imshow(packet.message, frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    client.shutdown()
    cv2.destroyAllWindows()


mainLoop()
