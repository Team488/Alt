import numpy as np
from typing import Optional
from . import utils
from .Capture import Capture
import cv2


class FileCapture(Capture):
    """
    Capture implementation that reads frames from a video file
    """

    def __init__(self, videoFilePath: str, flushTimeMS: int = -1) -> None:
        """
        Initialize a file capture with the specified video file path

        Args:
            videoFilePath: Path to the video file
            flushTimeMS: Time in milliseconds to flush the capture buffer (default: -1, no flush)
        """
        self.path: str = videoFilePath
        self.flushTimeMS: int = flushTimeMS
        self.cap: Optional[cv2.VideoCapture] = None

    def create(self) -> None:
        """
        Open the video file for reading

        Raises:
            BrokenPipeError: If the video file cannot be opened
        """
        self.cap = cv2.VideoCapture(self.path, cv2.CAP_V4L2)

        if not self.__testCapture(self.cap):
            raise BrokenPipeError(f"Failed to open video camera! {self.path=}")

    def __testCapture(self, cap: cv2.VideoCapture) -> bool:
        """
        Test if the capture can be read from

        Args:
            cap: The OpenCV VideoCapture object to test

        Returns:
            True if the capture can be read from, False otherwise
        """
        retTest = True
        if cap.isOpened():
            retTest, _ = cap.read()
        else:
            retTest = False
        return retTest

    def getMainFrame(self) -> np.ndarray:
        """
        Get the next color frame from the video

        Returns:
            The next frame as a numpy array
        """
        if self.cap is None:
            raise RuntimeError("Capture not created, call create() first")

        if self.flushTimeMS > 0:
            utils.flushCapture(self.cap, self.flushTimeMS)

        ret, frame = self.cap.read()
        if not ret or frame is None:
            # Return a black frame if we can't read from the capture
            return np.zeros((480, 640, 3), dtype=np.uint8)
        return frame

    def getFps(self) -> int:
        """
        Get the frames per second of the video

        Returns:
            The frames per second as an integer
        """
        if self.cap is None:
            raise RuntimeError("Capture not created, call create() first")

        return int(self.cap.get(cv2.CAP_PROP_FPS))

    def isOpen(self) -> bool:
        """
        Check if the capture is still open

        Returns:
            True if the capture is open, False otherwise
        """
        if self.cap is None:
            return False

        return self.cap.isOpened()

    def close(self) -> None:
        """
        Close the capture and release any resources
        """
        if self.cap is not None:
            self.cap.release()
            self.cap = None


def startDemo(videoFilePath: str) -> None:
    """
    Start a demo that shows frames from a video file

    Args:
        videoFilePath: Path to the video file to display
    """
    cap = FileCapture(videoFilePath)
    cap.create()

    while cap.isOpen():
        frame = cap.getMainFrame()

        cv2.imshow("Video", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.close()
