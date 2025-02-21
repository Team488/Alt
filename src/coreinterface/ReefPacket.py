import base64
import io
import time
import capnp
import cv2
import numpy as np
from typing import Dict
from assets.schemas import reefStatePacket_capnp


class ReefPacket:
    @staticmethod
    def createPacket(reefTrackerOutput : Dict[int,Dict[int,float]], message, timeStamp) -> reefStatePacket_capnp.ReefPacket:
        packet = reefStatePacket_capnp.ReefPacket.new_message()
        packet.message = message
        packet.timestamp = timeStamp
        flattenedOutput = ReefPacket.__flattenDict(reefTrackerOutput)
        packet_observations = packet.init("observations", len(flattenedOutput))

        for i in range(len(flattenedOutput)):
            observation = flattenedOutput[i]
            packet_detection = packet_observations[i]
            packet_detection.apriltagid = observation[0]
            packet_detection.branchindex = observation[1]
            packet_detection.openconfidence = observation[2]
        return packet
    
    @staticmethod
    def __flattenDict(reefTrackerOutput : Dict[int,Dict[int,float]]) -> list[tuple[int,int,float]]:
        flattened = []
        for atId, dict in reefTrackerOutput.items():
            for branchIdx, openconfidence in dict.items():
                flattened.append((atId,branchIdx,openconfidence))
        return flattened

    @staticmethod
    def toBase64(packet):
        # Write the packet to a byte string directly
        byte_str = packet.to_bytes()

        # Encode the byte string in base64 to send it as a string
        encoded_str = base64.b64encode(byte_str).decode("utf-8")
        return encoded_str

    @staticmethod
    def fromBase64(base64str):
        decoded_bytes = base64.b64decode(base64str)
        with reefStatePacket_capnp.ReefPacket.from_bytes(decoded_bytes) as packet:
            return packet

        return None

    @staticmethod
    def fromBytes(bytes):
        with reefStatePacket_capnp.ReefPacket.from_bytes(bytes) as packet:
            return packet

        return None

    def getFlattenedObservations(packet):
        # Decompress the JPEG data
        flattenedOutput = []
        for observation in packet.observations:
            flattenedOutput.append((observation.apriltagid,observation.branchindex,observation.openconfidence))
        return flattenedOutput


def test_packet():
    observations = {5 : {1 : .80, 2: .30}}
    packet = ReefPacket.createPacket(observations,"test",0)
    bytes = packet.to_bytes()
    decoded = ReefPacket.fromBytes(bytes)
    flattenedOutput = ReefPacket.getFlattenedObservations(packet)
    print(flattenedOutput)


if __name__ == "__main__":
    test_packet()
