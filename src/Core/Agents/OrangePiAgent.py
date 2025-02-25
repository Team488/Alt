from enum import Enum
import socket
from Core.Agents.Abstract.ReefTrackingAgentBase import ReefTrackingAgentBase
from tools import calibration
from tools.Constants import getCameraValues2024


class CameraName(Enum):
    REARRIGHT = "photonvisionrearright"
    REARLEFT = "photonvisionrearleft"
    FRONTRIGHT = "photonvisionfrontright"
    FRONTLEFT = "photonvisionfrontleft"


def getCameraName():
    name = socket.gethostname()
    return CameraName(name)


class OrangePiAgent(ReefTrackingAgentBase):
    """Agent -> CameraUsingAgentBase -> ReefTrackingAgentBase -> OrangePiAgent

    Agent to be run on the orange pis"""

    def __init__(self):
        self.device_name = CameraName.getCameraName().name
        # camera values
        cameraIntrinsics, _, _ = getCameraValues2024(self.device_name)

        super().__init__(
            cameraPath="/dev/color_camera",
            showFrames=False,
            cameraIntrinsics=cameraIntrinsics,
        )

    def create(self):
        super().create()
        self.Sentinel.info(f"Camera Name: {self.device_name}")

        # camera config
        self.calib = self.configOperator.getContent("camera_calib.json")

        # frame undistortion maps from calibration
        self.mapx, self.mapy = calibration.createMapXYForUndistortion(
            self.cameraIntrinsics.getHres(), self.cameraIntrinsics.getVres(), self.calib
        )

    def preprocessFrame(self, frame):
        return calibration.undistortFrame(frame, self.mapx, self.mapy)

    def getName(self):
        return "Orange_Pi_Process"

    def getDescription(self):
        return "Ingest_Camera_Run_Ai_Model_Return_Localized_Detections_And_NowAlsoTrackReef"

    def getIntervalMs(self):
        return 0
