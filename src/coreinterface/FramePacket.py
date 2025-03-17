import base64
import io
import time
import capnp
import cv2
import os
import numpy as np
from typing import Optional, Any

# We need to import the schema directly since it's not a Python module
schema_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                         "src", "assets", "schemas", "frameNetPacket.capnp")
frameNetPacket_capnp = capnp.load(schema_path)


class FramePacket:
    @staticmethod
    def createPacket(timeStamp: float, message: str, frame: np.ndarray) -> Any:
        """
        Create a new frame packet from the provided data
        
        Args:
            timeStamp: Timestamp for the frame
            message: A message string to include with the frame
            frame: The frame image as a numpy array
            
        Returns:
            A capnp DataPacket object containing the frame data
        """
        # Get the DataPacket class from the loaded schema
        DataPacketClass = frameNetPacket_capnp.DataPacket
        
        # Create a new message
        packet = DataPacketClass.new_message()
        packet.message = message
        packet.timestamp = timeStamp

        # Check that frame is a valid numpy array
        if not isinstance(frame, np.ndarray) or not hasattr(frame, 'shape') or len(frame.shape) < 2:
            raise ValueError("Frame must be a valid numpy array with at least 2 dimensions")

        # Compress the frame
        _, compressed_frame = cv2.imencode(
            ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        )  # You can adjust the quality

        # Initialize the frame in the packet
        packet_frame = packet.init("frame")
        
        # Get frame dimensions, handling the case of grayscale images (2D)
        if len(frame.shape) == 2:
            packet_frame.width = frame.shape[0]
            packet_frame.height = frame.shape[1]
            packet_frame.channels = 1
        else:  # Color image (3D)
            packet_frame.width = frame.shape[0]
            packet_frame.height = frame.shape[1]
            packet_frame.channels = frame.shape[2]
            
        packet_frame.init("data", len(compressed_frame))
        packet_frame.data = compressed_frame.tolist()

        return packet

    @staticmethod
    def toBase64(packet: Any) -> str:
        """
        Convert packet to base64 encoded string
        
        Args:
            packet: A capnp DataPacket object
            
        Returns:
            Base64 encoded string representation of the packet
        """
        # Write the packet to a byte string directly
        byte_str = packet.to_bytes()

        # Encode the byte string in base64 to send it as a string
        encoded_str = base64.b64encode(byte_str).decode("utf-8")
        return encoded_str

    @staticmethod
    def fromBase64(base64str: str) -> Optional[Any]:
        """
        Create a packet from a base64 encoded string
        
        Args:
            base64str: Base64 encoded string representation of a packet
            
        Returns:
            A capnp DataPacket object or None if decoding fails
        """
        decoded_bytes = base64.b64decode(base64str)
        with frameNetPacket_capnp.DataPacket.from_bytes(decoded_bytes) as packet:
            return packet
        return None

    @staticmethod
    def fromBytes(data_bytes: bytes) -> Optional[Any]:
        """
        Create a packet from bytes
        
        Args:
            data_bytes: Byte representation of a packet
            
        Returns:
            A capnp DataPacket object or None if decoding fails
        """
        with frameNetPacket_capnp.DataPacket.from_bytes(data_bytes) as packet:
            return packet
        return None

    @staticmethod
    def getFrame(packet: Any) -> Optional[np.ndarray]:
        """
        Extract and decompress the frame from a packet
        
        Args:
            packet: A capnp DataPacket object
            
        Returns:
            A numpy array containing the decompressed frame image, or None if extraction fails
        """
        try:
            # Check that packet has a frame
            if not hasattr(packet, 'frame') or not hasattr(packet.frame, 'data'):
                return None
                
            # Decompress the JPEG data
            compressed_frame = np.array(packet.frame.data, dtype=np.uint8)
            decompressed_frame = cv2.imdecode(compressed_frame, cv2.IMREAD_COLOR)
            return decompressed_frame
        except Exception as e:
            print(f"Error extracting frame from packet: {e}")
            return None


def test_packet() -> None:
    """
    Test function to demonstrate frame packet encoding and decoding
    """
    video_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "src", "assets", "video12qual25clipped.mp4"
    )
    
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        print(f"Error: Could not open video file at {video_path}")
        return
        
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        timeStamp = time.time()
        groundTruthPacket = FramePacket.createPacket(timeStamp, "TESTMESSAGE", frame)
        b64 = FramePacket.toBase64(groundTruthPacket)
        # assume some infinitely fast network transmission happened
        decodedPacket = FramePacket.fromBase64(b64)

        truthframe = FramePacket.getFrame(groundTruthPacket)
        decodedframe = FramePacket.getFrame(decodedPacket)

        if truthframe is not None and decodedframe is not None:
            cv2.imshow("True value", truthframe)
            cv2.imshow("Decoded value", decodedframe)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
            
    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    test_packet()
