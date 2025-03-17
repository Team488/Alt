import base64
import io
import time
import capnp
import cv2
import numpy as np
import os
from typing import Dict, List, Tuple, Any, Optional

# We need to import the schema directly since it's not a Python module
schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                         "src", "assets", "schemas", "reefStatePacket.capnp")
reefStatePacket_capnp = capnp.load(schema_path)


class ReefPacket:
    """
         Reef Face Structure

    l4-left (id 4)|  l4-right  (id 5)
         \        |        /
          \       |       /
    l3-left (id 2)|  l3-right  (id 3)
         \        |        /
          \       |       /
    l2-left (id 0)|  l2-right  (id 1)
         \        |        /
          \       |       /
      --------------------------
      |     April Tag id       |
      --------------------------




    """

    @staticmethod
    def createPacket(
        reefTrackerOutputCoral: Dict[int, Dict[int, float]],
        reefTrackerOutputAlgae: Dict[int, float],
        message: str,
        timeStamp: float,
    ) -> Any:
        """
        Reef tracker output is in format {atid: {branchid: openness conf, ....}, ....}
        Algae tracker output is in format {atid: {openness conf}, ....}
        """
        # Get the ReefPacket class from the loaded schema
        ReefPacketClass = reefStatePacket_capnp.ReefPacket
        
        # Create a new message
        packet = ReefPacketClass.new_message()
        packet.message = message
        packet.timestamp = timeStamp
        flattenedOutputCoral = ReefPacket.__flattenDictCoral(reefTrackerOutputCoral)

        packet_observations_reef = packet.init(
            "observationsReef", len(flattenedOutputCoral)
        )

        for i in range(len(flattenedOutputCoral)):
            # Explicitly unpack the tuple
            coral_id, branch_idx, open_conf = flattenedOutputCoral[i]
            packet_detection = packet_observations_reef[i]
            packet_detection.apriltagid = int(coral_id)
            packet_detection.branchindex = int(branch_idx)
            packet_detection.openconfidence = float(open_conf)

        flattenedOutputAlgae = ReefPacket.__flattenDictAlgae(reefTrackerOutputAlgae)

        packet_observations_algae = packet.init(
            "observationsAlgae", len(flattenedOutputAlgae)
        )

        for i in range(len(flattenedOutputAlgae)):
            # Explicitly unpack the tuple
            algae_id, algae_conf = flattenedOutputAlgae[i]
            packet_detection = packet_observations_algae[i]
            packet_detection.apriltagid = int(algae_id)
            packet_detection.occupiedconfidence = float(algae_conf)

        return packet

    @staticmethod
    def __flattenDictCoral(
        reefTrackerOutputCoral: Dict[int, Dict[int, float]]
    ) -> List[Tuple[int, int, float]]:
        flattened: List[Tuple[int, int, float]] = []
        for atId, value_dict in reefTrackerOutputCoral.items():
            for branchIdx, openconfidence in value_dict.items():
                flattened.append((int(atId), int(branchIdx), float(openconfidence)))
        return flattened

    @staticmethod
    def __flattenDictAlgae(
        reefTrackerOutputAlgae: Dict[int, float]
    ) -> List[Tuple[int, float]]:
        flattened: List[Tuple[int, float]] = []
        for atId, occupiedconfidence in reefTrackerOutputAlgae.items():
            flattened.append((int(atId), float(occupiedconfidence)))
        return flattened

    @staticmethod
    def toBase64(packet: Any) -> str:
        # Write the packet to a byte string directly
        byte_str = packet.to_bytes()

        # Encode the byte string in base64 to send it as a string
        encoded_str = base64.b64encode(byte_str).decode("utf-8")
        return encoded_str

    @staticmethod
    def fromBase64(base64str: str) -> Optional[Any]:
        decoded_bytes = base64.b64decode(base64str)
        with reefStatePacket_capnp.ReefPacket.from_bytes(decoded_bytes) as packet:
            return packet
        return None

    @staticmethod
    def fromBytes(data_bytes: bytes) -> Optional[Any]:
        with reefStatePacket_capnp.ReefPacket.from_bytes(data_bytes) as packet:
            return packet
        return None

    @staticmethod
    def getFlattenedObservations(packet: Any) -> Tuple[List[Tuple[int, int, float]], List[Tuple[int, float]]]:
        """
        Returns tuple of coral observations, and algae observations respectively
        Reef Observations as a list of (april tag id, branch index, confidence)
        Coral Observations as a list of (april tag id, confidence) \n
        NOTE: there is only one algae observation per reef face
        and that observation corresponds to either a low or high algae depending on the reef face april tag

        """
        # Add safety checks to handle cases where packet lacks expected attributes
        flattenedOutputCoral: List[Tuple[int, int, float]] = []
        if hasattr(packet, 'observationsReef'):
            for observation in packet.observationsReef:
                if hasattr(observation, 'apriltagid') and hasattr(observation, 'branchindex') and hasattr(observation, 'openconfidence'):
                    april_tag_id = int(observation.apriltagid)
                    branch_index = int(observation.branchindex)
                    open_confidence = float(observation.openconfidence)
                    flattenedOutputCoral.append((april_tag_id, branch_index, open_confidence))

        flattenedOutputAlgae: List[Tuple[int, float]] = []
        if hasattr(packet, 'observationsAlgae'):
            for observation in packet.observationsAlgae:
                if hasattr(observation, 'apriltagid') and hasattr(observation, 'occupiedconfidence'):
                    april_tag_id = int(observation.apriltagid)
                    occupied_confidence = float(observation.occupiedconfidence)
                    flattenedOutputAlgae.append((april_tag_id, occupied_confidence))

        return (flattenedOutputCoral, flattenedOutputAlgae)


def test_packet() -> None:
    observations: Dict[int, Dict[int, float]] = {5: {1: 0.80, 2: 0.30}}
    algae_observations: Dict[int, float] = {}
    packet = ReefPacket.createPacket(observations, algae_observations, "test", 0.0)
    data_bytes = packet.to_bytes()
    decoded = ReefPacket.fromBytes(data_bytes)
    flattenedOutput = ReefPacket.getFlattenedObservations(packet)
    print(flattenedOutput)


if __name__ == "__main__":
    test_packet()
