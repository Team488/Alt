import base64
import io
import time
from typing import Optional
import capnp
import cv2
from . import frameNetPacket_capnp
import numpy as np


class FramePacket:
    @staticmethod
    def createPacket(timeStamp : int, message : str, frame : np.ndarray) -> frameNetPacket_capnp.DataPacket:
        packet = frameNetPacket_capnp.DataPacket.new_message()
        packet.message = message
        packet.timestamp = timeStamp

        _, compressed_frame = cv2.imencode(
            ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        )  # You can adjust the quality

        packet_frame = packet.init("frame")
        packet_frame.width = frame.shape[0]
        packet_frame.height = frame.shape[1]
        packet_frame.channels = frame.shape[2]
        packet_frame.init("data", len(compressed_frame))

        packet_frame.data = compressed_frame.tolist()

        return packet

    @staticmethod
    def toBase64(packet : frameNetPacket_capnp.DataPacket):
        # Write the packet to a byte string directly
        byte_str = packet.to_bytes()

        # Encode the byte string in base64 to send it as a string
        encoded_str = base64.b64encode(byte_str).decode("utf-8")
        return encoded_str

    @staticmethod
    def fromBase64(base64str : str) -> Optional[frameNetPacket_capnp.DataPacket]:
        decoded_bytes = base64.b64decode(base64str)
        with frameNetPacket_capnp.DataPacket.from_bytes(decoded_bytes) as packet:
            return packet

        return None

    @staticmethod
    def fromBytes(bytes) -> Optional[frameNetPacket_capnp.DataPacket]:
        with frameNetPacket_capnp.DataPacket.from_bytes(bytes) as packet:
            return packet

        return None

    def getFrame(packet : frameNetPacket_capnp.DataPacket) -> np.ndarray:
        # Decompress the JPEG data
        compressed_frame = np.array(packet.frame.data, dtype=np.uint8)
        decompressed_frame = cv2.imdecode(compressed_frame, cv2.IMREAD_COLOR)
        return decompressed_frame


def test_packet() -> None:
    cap = cv2.VideoCapture("assets/video12qual25clipped.mp4")
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        timeStamp = time.time()
        groundTruthPacket = FramePacket.createPacket(timeStamp, "TESTMESSAGE", frame)
        b64 = FramePacket.toBase64(groundTruthPacket)
        # assume some infinitly fast network transmition happened. OOOooHHhhHHhh
        decodedPacket = FramePacket.fromBase64(b64)

        truthframe = FramePacket.getFrame(groundTruthPacket)
        decodedframe = FramePacket.getFrame(decodedPacket)

        cv2.imshow("True value", truthframe)
        cv2.imshow("Decoded value", decodedframe)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    test_packet()
