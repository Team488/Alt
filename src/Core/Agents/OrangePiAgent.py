import socket
from abstract.ObjectLocalizingAgentBase import ObjectLocalizingAgentBase
from enum import Enum
from tools.Constants import InferenceMode, getCameraValues
from tools import calibration


class CameraName(Enum):
    REARRIGHT = "photonvisionrearright"
    REARLEFT = "photonvisionrearleft"
    FRONTRIGHT = "photonvisionfrontright"
    FRONTLEFT = "photonvisionfrontleft"

    @staticmethod
    def getCameraName():
        name = socket.gethostname()
        return CameraName(name)


class OrangePiAgent(ObjectLocalizingAgentBase):
    """Agent -> LocalizingAgentBase -> FrameProcessingAgentBase -> OrangePiAgent

    Agent to be run on the orange pis"""

    def __init__(self):
        self.device_name = CameraName.getCameraName().name
        # camera values
        cameraIntrinsics, cameraExtrinsics, _ = getCameraValues(self.device_name)

        super().__init__(
            cameraPath="/dev/color_camera",
            cameraIntrinsics=cameraIntrinsics,
            cameraExtrinsics=cameraExtrinsics,
            inferenceMode=InferenceMode.RKNN2025INT8,
        )  # heres where we add our constants

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
        return "Ingest_Camera_Run_Ai_Model_Return_Localized_Detections"

    def getIntervalMs(self):
        return 0
