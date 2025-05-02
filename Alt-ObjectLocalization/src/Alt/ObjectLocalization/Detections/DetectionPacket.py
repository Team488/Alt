import base64

# necessary for the below import of the detection packet!
import capnp

import numpy as np
from Alt.Core.Units.Poses import Transform3d

from ..Localization.LocalizationResult import DeviceLocalizationResult, LocalizationResult
from . import detectionNetPacket_capnp


class DetectionPacket:
    @staticmethod
    # id,(absX,absY,absZ),conf,class_idx,features
    def createPacket(
        result: DeviceLocalizationResult,
        message : str,
        timeStamp,
    ) -> detectionNetPacket_capnp.DataPacket:
        
        numDetections = len(result.localizedResults)
        packet = detectionNetPacket_capnp.DataPacket.new_message()
        packet.message = message
        packet.deviceName = result.deviceUniqueName
        packet.timestamp = timeStamp
        packet_detections = packet.init("detections", numDetections)

        for i in range(numDetections):
            localizedResult = result.localizedResults[i]
            packet_detection = packet_detections[i]
            packet_detection.id = localizedResult.deepsort_id

            xyz = packet_detection.init("coordinates")
            xyz.x = int(localizedResult.location.x)
            xyz.y = int(localizedResult.location.y)
            xyz.z = int(localizedResult.location.z)

            packet_detection.confidence = float(localizedResult.conf)

            packet_detection.classidx = int(localizedResult.class_idx)

            packet_features = packet_detection.init("features")
            packet_features.init("data", len(localizedResult.features))[:] = localizedResult.features.astype(float)

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
    def toResults(packet) -> DeviceLocalizationResult:
        localizedResults = []

        for packet_detection in packet.detections:
            # Extract the detection id
            deepsort_id = packet_detection.id

            # Extract the coordinates (absX, absY, absZ)
            coordinates = packet_detection.coordinates
            x, y, z = (
                int(coordinates.x),
                int(coordinates.y),
                int(coordinates.z),
            )

            # Extract the confidence
            conf = float(packet_detection.confidence)

            # Extract the class_idx flag
            class_idx = int(packet_detection.classidx)

            # Extract the features
            packet_features = packet_detection.features
            features = np.array(packet_features.data, dtype=np.float64)


            # Combine into a tuple (id, (absX, absY, absZ), conf, class_idx, features)
            localizedResults.append(LocalizationResult(Transform3d(x, y, z), class_idx, conf, deepsort_id, features))

        return DeviceLocalizationResult(localizedResults, packet.deviceName)


def test_packet() -> None:
    packet = DetectionPacket.createPacket(
        [[10, (1, 2, 3), 0.6, 1, np.array([1, 2, 3, 4])]], "HELLO", 12345
    )
    print(packet)
    b64 = DetectionPacket.toBase64(packet)
    print("sucessful b64")
    outPacket = DetectionPacket.fromBase64(b64)
    print(outPacket)
    print(DetectionPacket.toResults(outPacket))


if __name__ == "__main__":
    DetectionPacket.test_packet()
