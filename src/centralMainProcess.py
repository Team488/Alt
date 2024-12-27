""" Process to run on orin """
import cv2
import argparse
import numpy as np
from tools.Constants import CameraIdOffsets
from XTABLES import XTablesClient
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.FramePacket import FramePacket
from mapinternals.CentralProcessor import CentralProcessor
from pathplanning.PathGenerator import PathGenerator
from tools.Constants import MapConstants


def getDetPackets(xtablesClient: XTablesClient):
    maxTimeout = 200
    keys = ("FRONTLEFT", "FRONTRIGHT", "REARLEFT", "REARRIGHT")
    detectionpackets = []
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
            print(f"------------------{key}------------------------")

    return detectionpackets


def getFramePackets(xtablesClient: XTablesClient):
    # maxTimeout = 1000
    # keys = ("FRONTLEFT", "FRONTRIGHT", "REARLEFT", "REARRIGHT")
    framepackets = []
    # for key in keys:
    #     print(f"Looking for key {key}")
    # frame
    rawB64 = xtablesClient.recv_next()[1]
    if rawB64 is not None and rawB64 and not rawB64.strip() == "null":
        dataPacket = FramePacket.fromBase64(rawB64)
        framepackets.append(dataPacket)
    return framepackets


def mainLoop(args):
    MapBottomCorner = (MapConstants.fieldWidth.value, MapConstants.fieldHeight.value)
    client = XTablesClient(server_port=1735)
    central = CentralProcessor.instance()
    pathGenerator = PathGenerator(central)
    pathName = "target_waypoints"
    currentPosition = tuple(np.divide(MapBottomCorner, 2))

    try:
        # client.subscribe("REARRIGHTframe")
        while True:
            detPackets = getDetPackets(client)
            if detPackets and detPackets[0][0]:
                print(detPackets)
                DetXY = detPackets[0][0][0][1][:2]  # x,y,z
                currentPosition = tuple(np.subtract(MapBottomCorner, DetXY))
                central.processFrameUpdate(
                    detPackets,
                    0.06,
                    positionOffset=(central.map.width // 2, central.map.height // 2, 0),
                )

            path = pathGenerator.generate(currentPosition)

            if path == None:
                client.executePutString(pathName, [])
            else:
                out = [{"x": waypoint[0], "y": waypoint[1]} for waypoint in path]
                client.executePutString(pathName, out)

            if args.show:
                # if args.fetchframe:
                #     try:
                #         framePackets = getFramePackets(client)
                #         for framePacket in framePackets:
                #             cv2.imshow(
                #                 framePacket.message, FramePacket.getFrame(framePacket)
                #             )
                #     except Exception as e:
                #         print(f"Error getting frame packets: {e}")
                #         break

                maps = central.map.getHeatMaps()
                cv2.imshow("Robot Map", maps[1])
                cv2.imshow("Game object Map", maps[0])
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    break
    except Exception as e:
        print(e)
    finally:
        print("Ending main process")
        cv2.destroyAllWindows()
        return


# print(time.time())
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    # Add an argument
    parser.add_argument("--show", type=bool, required=False, default=False)
    parser.add_argument("--fetchframe", type=bool, required=False, default=False)
    # Parse the argument
    args = parser.parse_args()
    mainLoop(args=args)
