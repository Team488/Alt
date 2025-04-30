from typing import Tuple, Optional
import numpy as np
from .depthCamera import depthCamera
from ..Parameters.CameraIntrinsics import CameraIntrinsics
from .Capture import CaptureWIntrinsics
from ..Constants.resolution import D435IResolution
from .tools.realsense2Helper import realsense2Helper


class D435Capture(depthCamera, CaptureWIntrinsics):
    """
    Capture implementation for Intel RealSense D435 depth camera
    """

    def __init__(self, name : str, res: D435IResolution, realsenseSerialId=None) -> None:
        """
        Initialize a D435 capture with the specified resolution

        Args:
            res: The resolution setting for the camera
        """
        super().__init__(name)
        self.res: D435IResolution = res
        self.realSenseSerialId = realsenseSerialId
        self.realsenseHelper: Optional[realsense2Helper] = None

    def create(self) -> None:
        """
        Initialize the RealSense camera
        """
        self.realsenseHelper = realsense2Helper(self.res, self.realSenseSerialId)
        intr: CameraIntrinsics = self.realsenseHelper.getCameraIntrinsics()
        super().setIntrinsics(intr)

    def getMainFrame(self) -> np.ndarray:
        """
        Get the color frame from the camera

        Returns:
            The color frame as a numpy array
        """
        if self.realsenseHelper is None:
            raise RuntimeError("Capture not created, call create() first")

        return self.realsenseHelper.getDepthAndColor()[1]

    def getFps(self) -> int:
        """
        Get the camera frames per second

        Returns:
            Camera frame rate
        """
        if self.realsenseHelper is None:
            raise RuntimeError("Capture not created, call create() first")

        return self.realsenseHelper.getFps()

    def getDepthFrame(self) -> np.ndarray:
        """
        Get the depth frame from the camera

        Returns:
            The depth frame as a numpy array
        """
        return self.getDepthAndColorFrame()[0]  # linked together

    def getDepthAndColorFrame(self) -> Tuple[np.ndarray, np.ndarray]:
        """
        Get both the depth and color frames from the camera

        Returns:
            A tuple containing (depth_frame, color_frame)
        """
        if self.realsenseHelper is None:
            raise RuntimeError("Capture not created, call create() first")

        return self.realsenseHelper.getDepthAndColor()

    def isOpen(self) -> bool:
        """
        Check if the camera is still open

        Returns:
            True if the camera is open, False otherwise
        """
        if self.realsenseHelper is None:
            return False

        return self.realsenseHelper.isOpen()

    def close(self) -> None:
        """
        Close the camera and release resources
        """
        if self.realsenseHelper is not None:
            self.realsenseHelper.close()
            self.realsenseHelper = None


def startDemo() -> None:
    """
    Start a demo showing depth and color frames from the D435 camera
    """
    import cv2

    cap = D435Capture("test", D435IResolution.RS480P)
    cap.create()

    while cap.isOpen():
        depth, color = cap.getDepthAndColorFrame()
        cv2.imshow("depth", depth)
        cv2.imshow("color", color)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.close()
