from typing import Union, Optional, Any
import cv2
import numpy as np
from .Capture import ConfigurableCapture
from ..Parameters.Intrinsics import CameraIntrinsics
from . import utils


class ConfigurableCameraCapture(ConfigurableCapture):
    """
    A configurable camera capture implementation for USB/built-in cameras
    """

    def __init__(
        self,
        uniqueId: str,
        cameraPath: Union[str, int],
        cameraIntrinsics: CameraIntrinsics,
        flushTimeMS: int = -1,
    ) -> None:
        """
        Initialize a configurable camera capture

        Args:
            uniqueId: Unique identifier for this camera
            cameraPath: Camera device path (string) or index (integer)
            cameraIntrinsics: Camera intrinsic parameters
            flushTimeMS: Time in milliseconds to flush the capture buffer (default: -1, no flush)
        """
        super().__init__()
        self.uniqueId: str = uniqueId
        self.path: Union[str, int] = cameraPath
        self.flushTimeMS: int = flushTimeMS
        self.cap: Optional[cv2.VideoCapture] = None
        super().setIntrinsics(cameraIntrinsics)

    def create(self) -> None:
        """
        Open the camera for capture

        Raises:
            BrokenPipeError: If the camera cannot be opened
        """
        self.cap = cv2.VideoCapture(self.path, cv2.CAP_V4L2)
        if not self.__testCapture(self.cap):
            raise BrokenPipeError(f"Failed to open video camera! {self.path=}")

        # add configurable settings
        # Use getattr to satisfy mypy
        # video_writer_fourcc = getattr(cv2, 'VideoWriter_fourcc')
        # fourcc = video_writer_fourcc(*"MJPG")  # or 'XVID', 'MP4V'
        # self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
        CameraIntrinsics.setCapRes(self.cameraIntrinsics, self.cap)

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
        Get a color frame from the camera

        Returns:
            The color frame as a numpy array
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
        Get the camera frames per second

        Returns:
            The camera frame rate
        """
        if self.cap is None:
            raise RuntimeError("Capture not created, call create() first")

        return int(self.cap.get(cv2.CAP_PROP_FPS))

    def isOpen(self) -> bool:
        """
        Check if the camera is still open

        Returns:
            True if the camera is open, False otherwise
        """
        if self.cap is None:
            return False

        return self.cap.isOpened()

    def close(self) -> None:
        """
        Close the camera and release resources
        """
        if self.cap is not None:
            self.cap.release()
            self.cap = None

    def getCameraPath(self) -> Union[str, int]:
        """
        Get the camera path or index

        Returns:
            The camera path or index
        """
        return self.path

    def getUniqueCameraIdentifier(self) -> str:
        """
        Get a unique identifier for this camera

        Returns:
            A unique identifier string
        """
        identifier = self.uniqueId  # TODO add more?
        return identifier

    def updateIntrinsics(self, newIntrinsics: CameraIntrinsics) -> None:
        """
        Update the camera intrinsics and apply the new settings

        Args:
            newIntrinsics: New camera intrinsic parameters
        """
        super().setIntrinsics(newIntrinsics)
        if self.cap is not None:
            CameraIntrinsics.setCapRes(newIntrinsics, self.cap)
