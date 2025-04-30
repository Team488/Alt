from typing import Tuple, Optional
import numpy as np
from .depthCamera import depthCamera
from .Capture import CaptureWIntrinsics
from ..Constants.resolution import OAKDLITEResolution
from .tools.depthAiHelper import DepthAIHelper


class OAKCapture(depthCamera, CaptureWIntrinsics):
    """
    Capture implementation for OpenCV AI Kit (OAK-D) camera
    """

    def __init__(self, name : str, res: OAKDLITEResolution) -> None:
        """
        Initialize OAK capture with specified resolution

        Args:
            res: Resolution setting for the camera
        """
        super().__init__(name)
        self.res: OAKDLITEResolution = res
        self.depthAiHelper: Optional[DepthAIHelper] = None

    def create(self) -> None:
        """
        Initialize the OAK camera
        """
        self.depthAiHelper = DepthAIHelper(self.res)
        super().setIntrinsics(self.depthAiHelper.getColorIntrinsics())

    def getDepthAndColorFrame(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get both depth and color frames from the camera

        Returns:
            A tuple containing (depth_frame, color_frame)
        """
        if self.depthAiHelper is None:
            raise RuntimeError("Capture not created, call create() first")

        return (self.depthAiHelper.getDepthFrame(), self.depthAiHelper.getColorFrame())

    def getDepthFrame(self) -> np.ndarray:
        """
        Get the depth frame from the camera

        Returns:
            The depth frame as a numpy array
        """
        if self.depthAiHelper is None:
            raise RuntimeError("Capture not created, call create() first")

        return self.depthAiHelper.getDepthFrame()

    def getMainFrame(self) -> np.ndarray:
        """
        Get the color frame from the camera

        Returns:
            The color frame as a numpy array
        """
        if self.depthAiHelper is None:
            raise RuntimeError("Capture not created, call create() first")

        return self.depthAiHelper.getColorFrame()

    def getFps(self) -> int:
        """
        Get the camera frames per second

        Returns:
            Camera frame rate
        """
        if self.depthAiHelper is None:
            raise RuntimeError("Capture not created, call create() first")

        return self.depthAiHelper.getFps()

    def isOpen(self) -> bool:
        """
        Check if the camera is still open

        Returns:
            True if the camera is open, False otherwise
        """
        if self.depthAiHelper is None:
            return False

        return self.depthAiHelper.isOpen()

    def close(self) -> None:
        """
        Close the camera and release resources
        """
        if self.depthAiHelper is not None:
            self.depthAiHelper.close()
            self.depthAiHelper = None


def startDemo() -> None:
    """
    Start a demo showing depth and color frames from the OAK camera
    """
    import cv2

    cap = OAKCapture(OAKDLITEResolution.OAK1080P)
    cap.create()

    while cap.isOpen():
        depth, color = cap.getDepthAndColorFrame()
        cv2.imshow("depth", depth)
        cv2.imshow("color", color)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.close()
