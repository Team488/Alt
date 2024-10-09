import base64
import io
import capnp
from assets.schemas import detectionNetPacket_capnp
import numpy as np
import traceback
import sys


class DetectionPacket:
    @staticmethod
    # id,(absX,absY,absZ),conf,isRobot,features
    def createPacket(
        detections: list[list[int, tuple[int, int, int], float, bool, np.ndarray]]
    ) -> detectionNetPacket_capnp.DataPacket:
        numDetections = len(detections)
        packet = detectionNetPacket_capnp.DataPacket.new_message()
        packet_detections = packet.init("detections", numDetections)

        for i in range(numDetections):
            detection = detections[i]
            packet_detection = packet_detections[0]
            packet_detection.id = detection[0]
            xyz = packet_detection.init("coordinates")
            coords = detection[1]
            xyz.x = coords[0]
            xyz.y = coords[1]
            xyz.z = coords[2]
            packet_detection.confidence = float(detection[2])
            packet_detection.isRobot = detection[3]
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


if __name__ == "__main__":
    packet = DetectionPacket.createPacket(
        [[10, (1, 2, 3), 0.6, True, np.array([1, 2, 3, 4])]]
    )
    print(packet)
    b64 = DetectionPacket.toBase64(packet)
    print("sucessful b64")
    outPacket = DetectionPacket.fromBase64(b64)
    print(outPacket)
