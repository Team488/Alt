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
    def createPacket(
        reefTrackerOutputCoral: Dict[int, Dict[int, float]],
        reefTrackerOutputAlgae: Dict[int, float],
        message,
        timeStamp,
    ) -> reefStatePacket_capnp.ReefPacket:
        packet = reefStatePacket_capnp.ReefPacket.new_message()
        packet.message = message
        packet.timestamp = timeStamp
        flattenedOutputCoral = ReefPacket.__flattenDictCoral(reefTrackerOutputCoral)

        packet_observations_reef = packet.init(
            "observationsReef", len(flattenedOutputCoral)
        )

        for i in range(len(flattenedOutputCoral)):
            observation = flattenedOutputCoral[i]
            packet_detection = packet_observations_reef[i]
            packet_detection.apriltagid = observation[0]
            packet_detection.branchindex = observation[1]
            packet_detection.openconfidence = float(observation[2])

        flattenedOutputAlgae = ReefPacket.__flattenDictAlgae(reefTrackerOutputAlgae)

        packet_observations_algae = packet.init(
            "observationsAlgae", len(flattenedOutputAlgae)
        )

        for i in range(len(flattenedOutputAlgae)):
            observation = flattenedOutputAlgae[i]
            packet_detection = packet_observations_algae[i]
            packet_detection.apriltagid = observation[0]
            packet_detection.occupiedconfidence = float(observation[1])

        return packet

    @staticmethod
    def __flattenDictCoral(
        reefTrackerOutputCoral: Dict[int, Dict[int, float]]
    ) -> list[tuple[int, int, float]]:
        flattened = []
        for atId, dict in reefTrackerOutputCoral.items():
            for branchIdx, openconfidence in dict.items():
                flattened.append((atId, branchIdx, openconfidence))
        return flattened

    @staticmethod
    def __flattenDictAlgae(
        reefTrackerOutputAlgae: Dict[int, float]
    ) -> list[tuple[int, float]]:
        flattened = []
        for atId, occupiedconfidence in reefTrackerOutputAlgae.items():
            flattened.append((atId, occupiedconfidence))
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

    def getFlattenedObservations(packet) -> list[tuple[int, int, float]]:
        """Observations as a list of (april tag id, branch index, confidence)"""
        # Decompress the JPEG data
        flattenedOutputReef = []
        for observation in packet.observationsReef:
            flattenedOutputReef.append(
                (
                    observation.apriltagid,
                    observation.branchindex,
                    observation.openconfidence,
                )
            )

        flattenedOutputAlgae = []
        for observation in packet.observationsAlgae:
            flattenedOutputAlgae.append(
                (observation.apriltagid, observation.occupiedconfidence)
            )

        return flattenedOutputReef, flattenedOutputAlgae


def test_packet():
    observations = {5: {1: 0.80, 2: 0.30}}
    packet = ReefPacket.createPacket(observations, {}, "test", 0)
    bytes = packet.to_bytes()
    decoded = ReefPacket.fromBytes(bytes)
    flattenedOutput = ReefPacket.getFlattenedObservations(packet)[0]
    print(flattenedOutput)


if __name__ == "__main__":
    test_packet()
