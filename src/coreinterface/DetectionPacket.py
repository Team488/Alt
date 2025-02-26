import base64
import io
import capnp
from assets.schemas import detectionNetPacket_capnp
import numpy as np
import traceback
import sys


class DetectionPacket:
    @staticmethod
    # id,(absX,absY,absZ),conf,class_idx,features
    def createPacket(
        detections: list[list[int, tuple[int, int, int], float, int, np.ndarray]],
        message,
        timeStamp,
    ) -> detectionNetPacket_capnp.DataPacket:
        numDetections = len(detections)
        packet = detectionNetPacket_capnp.DataPacket.new_message()
        packet.message = message
        packet.timestamp = timeStamp
        packet_detections = packet.init("detections", numDetections)

        for i in range(numDetections):
            detection = detections[i]
            packet_detection = packet_detections[i]

            packet_detection.id = detection[0]

            xyz = packet_detection.init("coordinates")
            coords = detection[1]
            xyz.x = int(coords[0])
            xyz.y = int(coords[1])
            xyz.z = int(coords[2])

            packet_detection.confidence = float(detection[2])

            packet_detection.classidx = int(detection[3])

            features = detection[4]
            packet_features = packet_detection.init("features")

            featurelen = len(features)
            packet_features.length = featurelen

            packet_features_data = packet_features.init("data", featurelen)
            for j in range(featurelen):
                packet_features_data[j] = float(features[j])

        return packet

    @staticmethod
    def toBase64(packet):
        # Write the packet to a byte string directly
        byte_str = packet.to_bytes()

        # Encode the byte string in base64 to send it as a string
        encoded_str = base64.b64encode(byte_str).decode("utf-8")
        return encoded_str

    @staticmethod
    def fromBase64(base64str):
        decoded_bytestr = base64.b64decode(base64str)
        with detectionNetPacket_capnp.DataPacket.from_bytes(decoded_bytestr) as packet:
            return packet
        return None

    @staticmethod
    def fromBytes(bytes):
        with detectionNetPacket_capnp.DataPacket.from_bytes(bytes) as packet:
            return packet
        return None

    @staticmethod
    def toDetections(packet):
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


if __name__ == "__main__":
    DetectionPacket.test_packet()
