import base64
import io
import capnp
import os
import numpy as np
import traceback
import sys
from typing import List, Tuple, Optional, Any, Union

# We need to import the schema directly since it's not a Python module
schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                         "src", "assets", "schemas", "detectionNetPacket.capnp")
detectionNetPacket_capnp = capnp.load(schema_path)


class DetectionPacket:
    @staticmethod
    # id,(absX,absY,absZ),conf,class_idx,features
    def createPacket(
        detections: List[List[Union[int, Tuple[int, int, int], float, np.ndarray]]],
        message: str,
        timeStamp: float,
    ) -> Any:
        numDetections = len(detections)
        packet = detectionNetPacket_capnp.DataPacket.new_message()
        packet.message = message
        packet.timestamp = timeStamp
        packet_detections = packet.init("detections", numDetections)

        for i in range(numDetections):
            detection = detections[i]
            packet_detection = packet_detections[i]

            # Process the detection by index since typing is complex
            # First item is ID
            id_val = detection[0]
            if isinstance(id_val, (int, float)):
                packet_detection.id = int(id_val)
            else:
                packet_detection.id = 0

            # Second item is coordinates tuple
            xyz = packet_detection.init("coordinates")
            coords = detection[1]
            if isinstance(coords, tuple) and len(coords) >= 3:
                xyz.x = int(coords[0])
                xyz.y = int(coords[1])
                xyz.z = int(coords[2])
            else:
                xyz.x = 0
                xyz.y = 0
                xyz.z = 0
            
            # Third item is confidence
            conf_val = detection[2]
            if isinstance(conf_val, (int, float)):
                packet_detection.confidence = float(conf_val)
            else:
                packet_detection.confidence = 0.0

            # Fourth item is class index
            class_idx = detection[3]
            if isinstance(class_idx, (int, float)):
                packet_detection.classidx = int(class_idx)
            else:
                packet_detection.classidx = 0

            # Fifth item is features array
            features = detection[4]
            packet_features = packet_detection.init("features")

            # Make sure features is a numpy array or an object with a length
            if hasattr(features, "__len__"):
                featurelen = len(features)
                packet_features.length = featurelen

                packet_features_data = packet_features.init("data", featurelen)
                # Process features based on its type
                if isinstance(features, np.ndarray):
                    for j in range(featurelen):
                        packet_features_data[j] = float(features[j])
                elif isinstance(features, (list, tuple)):
                    # Handle as list/tuple
                    for j, feature_val in enumerate(features):
                        packet_features_data[j] = float(feature_val)
                else:
                    # Fallback for unknown types
                    for j in range(featurelen):
                        packet_features_data[j] = 0.0

        return packet

    @staticmethod
    def toBase64(packet: Any) -> str:
        # Write the packet to a byte string directly
        byte_str = packet.to_bytes()

        # Encode the byte string in base64 to send it as a string
        encoded_str = base64.b64encode(byte_str).decode("utf-8")
        return encoded_str

    @staticmethod
    def fromBase64(base64str: str) -> Optional[Any]:
        decoded_bytestr = base64.b64decode(base64str)
        with detectionNetPacket_capnp.DataPacket.from_bytes(decoded_bytestr) as packet:
            return packet
        return None

    @staticmethod
    def fromBytes(byte_data: bytes) -> Optional[Any]:
        with detectionNetPacket_capnp.DataPacket.from_bytes(byte_data) as packet:
            return packet
        return None

    @staticmethod
    def toDetections(packet: Any) -> List[List[Union[int, Tuple[int, int, int], float, np.ndarray]]]:
        detections = []

        for packet_detection in packet.detections:
            # Extract the detection id
            detection_id = packet_detection.id

            # Extract the coordinates (absX, absY, absZ)
            coordinates = packet_detection.coordinates
            absX, absY, absZ = (
                int(coordinates.x),
                int(coordinates.y),
                int(coordinates.z),
            )

            # Extract the confidence
            confidence = float(packet_detection.confidence)

            # Extract the class_idx flag
            class_idx = int(packet_detection.classidx)

            # Extract the features
            packet_features = packet_detection.features
            features = np.array([float(f) for f in packet_features.data])

            # Combine into a tuple (id, (absX, absY, absZ), conf, class_idx, features)
            detection = [
                detection_id,
                (absX, absY, absZ),
                confidence,
                class_idx,
                features,
            ]
            detections.append(detection)

        return detections


def test_packet() -> None:
    packet = DetectionPacket.createPacket(
        [[10, (1, 2, 3), 0.6, 1, np.array([1, 2, 3, 4])]], "HELLO", 12345
    )
    print(packet)
    b64 = DetectionPacket.toBase64(packet)
    print("sucessful b64")
    outPacket = DetectionPacket.fromBase64(b64)
    print(outPacket)
    print(DetectionPacket.toDetections(outPacket))


# Remove class method reference to test_packet
if __name__ == "__main__":
    test_packet()
