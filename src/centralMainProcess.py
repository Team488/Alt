""" Process to run on orin """
import cv2
from tools.Constants import CameraExtrinsics, CameraIntrinsics, CameraIdOffsets
from coreinterface.XTablesClient import XTablesClient
from coreinterface.DataPacket import DataPacket
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
            cleaned_json = rawJson.replace('\\"', '"')
            print(cleaned_json[:100])
            dataPacket = DataPacket.decode(cleaned_json)
            packets.append(dataPacket)

    return packets


def mainLoop():
    client = XTablesClient()
    # frameProcessors = [LocalFrameProcessor(CameraIntrinsics.OV9782COLOR,CameraExtrinsics.)]

    # frameProcessor =
    while True:
        packets: list[DataPacket] = getPackets(client)
        for packet in packets:
            cv2.imshow(packet.message, packet.frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    client.shutdown()
    cv2.destroyAllWindows()


mainLoop()
