import numpy as np
from typing import Optional
from . import utils
from .Capture import Capture

import cv2
from Alt.Core import Platform, DEVICEPLATFORM
DefaultUseV4L2 = DEVICEPLATFORM == Platform.LINUX

class OpenCVCapture(Capture):
    """
    """

    def __init__(self, name : str, capturePath: str, useV4L2Backend : bool = DefaultUseV4L2, flushTimeMS: int = -1) -> None:
        """
        Initialize a file capture with the specified video file path

        Args:
            videoFilePath: Path to the video file
            flushTimeMS: Time in milliseconds to flush the capture buffer (default: -1, no flush)
        """
        super().__init__(name)
        self.path: str = capturePath
        self.useV4L2Backend = useV4L2Backend
        self.flushTimeMS: int = flushTimeMS
        self.cap: Optional[cv2.VideoCapture] = None

    def create(self) -> None:
        """
        Open the video file for reading

        Raises:
            BrokenPipeError: If the video file cannot be opened
        """
        if self.useV4L2Backend:
            self.cap = cv2.VideoCapture(self.path, cv2.CAP_V4L2)
        else:
            self.cap = cv2.VideoCapture(self.path)

        if not self.__testCapture(self.cap):
            raise BrokenPipeError(f"Failed to open video camera! {self.path=} {self.useV4L2Backend=}")

                

    def __testCapture(self, cap: cv2.VideoCapture) -> bool:
        """
        Test if the capture can be read from

        Args:
            cap: The OpenCV VideoCapture object to test

        Returns:
            True if the capture can be read from, False otherwise
        """
        retTest = False

        if cap.isOpened():
            retTest, _ = cap.read()

        return retTest
        
    def __ensureCap(self) -> None:
        if self.cap is None:
            raise RuntimeError("Capture not created, call create() first")

    def getMainFrame(self) -> np.ndarray:
        """
        Get the next color frame from the video

        Returns:
            The next frame as a numpy array
        """
        self.__ensureCap()

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
        self.__ensureCap()

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

    def setFps(self, fps : int) -> bool:
        self.__ensureCap()
        return self.cap.set(cv2.CAP_PROP_FPS, fps)
    
    def setVideoWriter(self, videoWriter: str = "MJPG") -> bool:
        self.__ensureCap()
        return self.cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*videoWriter))
    
    def setWidth(self, width : int) -> bool:
        self.__ensureCap()
        return self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)

    def setHeight(self, height : int) -> bool:
        self.__ensureCap()
        return self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
    
    def setAutoExposure(self, autoExposure : bool, manualExposure : float = None) -> bool:
        self.__ensureCap()
        propertySet = self.cap.set(cv2.CAP_PROP_AUTO_EXPOSURE, 0.75 if autoExposure else 0.25)
        
        if not autoExposure:
            if manualExposure is None:
                raise RuntimeError("If you are setting autoExposure to false, you must provide a manualExposure!")
            
            manualSet = self.capture.cap.set(
                cv2.CAP_PROP_EXPOSURE, manualExposure
            )

            propertySet = propertySet and manualSet
        
        return propertySet


