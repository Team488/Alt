import json
import cv2
import numpy as np


class DataPacket:
    def __init__(self, timestamp, message, frame):
        self.timestamp = timestamp  # Expected to be a float from time.time()
        self.message = message  # A string message
        self.frame = frame  # An OpenCV frame (numpy array)

    def encode(self):
        # Convert the frame to a list of pixel values
        _, buffer = cv2.imencode(".jpg", self.frame)
        frame_data = buffer.tobytes()

        # Convert the frame bytes to a base64 string
        frame_base64 = np.frombuffer(frame_data, dtype=np.uint8).tolist()

        # Create a dictionary to hold the data
        data = {
            "timestamp": self.timestamp,
            "message": self.message,
            "frame": frame_base64,
        }

        # Convert the dictionary to a JSON string
        json_string = json.dumps(data)
        return json_string

    @classmethod
    def decode(cls, json_string):
        # Decode the JSON string into a dictionary
        data = json.loads(json_string)

        # Convert the base64 list back to bytes
        frame_data = np.array(data["frame"], dtype=np.uint8)

        # Decode the image from the byte array
        frame = cv2.imdecode(frame_data, cv2.IMREAD_COLOR)

        # Create an instance of the class with the decoded data
        return cls(data["timestamp"], data["message"], frame)
