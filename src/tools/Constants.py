from enum import Enum
from typing import Any

import math
import numpy as np
from scipy.spatial.transform import Rotation


class YOLOTYPE(Enum):
    V11 = "v11"
    V8 = "v8"
    V5 = "v5"


class Backend(Enum):
    RKNN = "rknn"
    ONNX = "onnx"
    ULTRALYTICS = "ultralytics"


class InferenceMode(Enum):
    ONNX2024 = (
        "assets/yolov5s_fp32.onnx",
        "yolov5s-onnx-fp32",
        ("Robot", "Note"),
        2024,
        Backend.ONNX,
        YOLOTYPE.V5,
    )
    ONNXSMALL2025 = (
        "assets/yolov11s_fp32.onnx",
        "yolov11s-onnx-fp32",
        ("Algae", "Coral"),
        2025,
        Backend.ONNX,
        YOLOTYPE.V11,
    )
    ONNXMEDIUM2025 = (
        "assets/yolov11m_fp32.onnx",
        "yolov11m-onnx-fp32",
        ("Algae", "Coral"),
        2025,
        Backend.ONNX,
        YOLOTYPE.V11,
    )
    ONNX2024 = (
        "assets/yolov5s_fp32.onnx",
        "yolov5s-onnx-fp32",
        ("Robot", "Note"),
        2024,
        Backend.ONNX,
        YOLOTYPE.V5,
    )
    ONNXSMALL2025 = (
        "assets/yolov11s_fp32.onnx",
        "yolov11s-onnx-fp32",
        ("Algae", "Coral"),
        2025,
        Backend.ONNX,
        YOLOTYPE.V11,
    )
    ONNXMEDIUM2025 = (
        "assets/yolov11m_fp32.onnx",
        "yolov11m-onnx-fp32",
        ("Algae", "Coral"),
        2025,
        Backend.ONNX,
        YOLOTYPE.V11,
    )

    RKNN2024FP32 = (
        "assets/yolov5s_fp32.rknn",
        "yolov5s-rknn-fp32",
        ("Robot", "Note"),
        2024,
        Backend.RKNN,
        YOLOTYPE.V5,
    )
    RKNN2025INT8 = (
        "assets/yolov11s_int8.rknn",
        "yolov11s-rknn-int8",
        ("Algae", "Coral"),
        2025,
        Backend.RKNN,
        YOLOTYPE.V11,
    )
    RKNN2024FP32 = (
        "assets/yolov5s_fp32.rknn",
        "yolov5s-rknn-fp32",
        ("Robot", "Note"),
        2024,
        Backend.RKNN,
        YOLOTYPE.V5,
    )
    RKNN2025INT8 = (
        "assets/yolov11s_int8.rknn",
        "yolov11s-rknn-int8",
        ("Algae", "Coral"),
        2025,
        Backend.RKNN,
        YOLOTYPE.V11,
    )

    ULTRALYTICSSMALL2025 = (
        "assets/yolov11s_fp32.pt",
        "yolov11s-pytorch-fp32",
        ("Algae", "Coral"),
        2025,
        Backend.ULTRALYTICS,
        YOLOTYPE.V11,
    )
    ULTRALYTICSMED2025 = (
        "assets/yolov11m_fp32.pt",
        "yolov11s-pytorch-fp32",
        ("Algae", "Coral"),
        2025,
        Backend.ULTRALYTICS,
        YOLOTYPE.V11,
    )

    ULTRALYTICSSMALL2025 = (
        "assets/yolov11s_fp32.pt",
        "yolov11s-pytorch-fp32",
        ("Algae", "Coral"),
        2025,
        Backend.ULTRALYTICS,
        YOLOTYPE.V11,
    )
    ULTRALYTICSMED2025 = (
        "assets/yolov11m_fp32.pt",
        "yolov11s-pytorch-fp32",
        ("Algae", "Coral"),
        2025,
        Backend.ULTRALYTICS,
        YOLOTYPE.V11,
    )

    # TORCH todo!

    def getModelPath(self) -> str:
        return self.value[0]

    def getName(self):
        return self.value[1]

    def getLabels(self):
        return self.value[2]

    def getYear(self):
        return self.value[3]

    def getBackend(self):
        return self.value[4]

    def getYoloType(self):
        return self.value[5]


class Object(Enum):
    ALGAE = "a"
    CORAL = "c"
    NOTE = "n"
    ROBOT = "r"


class CameraExtrinsics:
    #   {PositionName} = ((offsetX(in),offsetY(in),offsetZ(in)),(yawOffset(deg),pitchOffset(deg)))
    def getOffsetXIN(self):
        return self.value[0][0]

    def getOffsetXCM(self):
        return self.value[0][0] * 2.54

    def getOffsetYIN(self) -> float:
        return self.value[0][1]

    def getOffsetYCM(self):
        return self.value[0][1] * 2.54

    def getOffsetZIN(self) -> float:
        return self.value[0][2]

    def getOffsetZCM(self):
        return self.value[0][2] * 2.54  # Fixed typo (was using Y instead of Z)

    def getYawOffset(self) -> float:
        return self.value[1][0]

    def getPitchOffset(self) -> float:
        return self.value[1][1]

    def getYawOffsetAsRadians(self) -> float:
        return math.radians(self.value[1][0])

    def getPitchOffsetAsRadians(self) -> float:
        return math.radians(self.value[1][1])

    def get4x4AffineMatrix(self):
        """Returns a 4x4 affine transformation matrix for the camera extrinsics"""
        x, y, z = self.value[0]
        yaw, pitch = map(math.radians, self.value[1])  # Convert degrees to radians

        # Create rotation matrix (assuming yaw around Z, pitch around Y)
        rotation_matrix = Rotation.from_euler("zy", [yaw, pitch]).as_matrix()

        # Construct the 4x4 transformation matrix
        affine_matrix = np.eye(4)
        affine_matrix[:3, :3] = rotation_matrix
        affine_matrix[:3, 3] = [x, y, z]  # Set translation

        return affine_matrix

    def get4x4AffineMatrixMeters(self):
        """Returns a 4x4 affine transformation matrix for the camera extrinsics"""
        x, y, z = map(lambda x: x * 0.0254, self.value[0])
        yaw, pitch = map(math.radians, self.value[1])  # Convert degrees to radians

        # Create rotation matrix (assuming yaw around Z, pitch around Y)
        rotation_matrix = Rotation.from_euler("zy", [yaw, pitch]).as_matrix()

        # Construct the 4x4 transformation matrix
        affine_matrix = np.eye(4)
        affine_matrix[:3, :3] = rotation_matrix
        affine_matrix[:3, 3] = [x, y, z]  # Set translation

        return affine_matrix


class ColorCameraExtrinsics2024(CameraExtrinsics, Enum):
    #   {PositionName} = ((offsetX(in),offsetY(in),offsetZ(in)),(yawOffset(deg),pitchOffset(deg)))
    FRONTLEFT = ((13.779, 13.887, 10.744), (80, -3))
    FRONTRIGHT = ((13.779, -13.887, 10.744), (280, -3))
    REARLEFT = ((-13.116, 12.853, 10.52), (215, -3.77))
    REARRIGHT = ((-13.116, -12.853, 10.52), (145, -3.77))
    DEPTHLEFT = ((13.018, 2.548, 19.743), (24, -17))
    DEPTHRIGHT = ((13.018, -2.548, 19.743), (-24, -17))
    NONE = ((0, 0, 0), (0, 0))


class ColorCameraExtrinsics2025(CameraExtrinsics, Enum):
    #   {PositionName} = ((offsetX(in),offsetY(in),offsetZ(in)),(yawOffset(deg),pitchOffset(deg)))
    # TODO
    pass


class ATCameraExtrinsics(CameraExtrinsics):
    def getPhotonCameraName(self):
        return self.value[2]


class ATCameraExtrinsics2024(ATCameraExtrinsics, Enum):
    #   {PositionName} = ((offsetX(in),offsetY(in),offsetZ(in)),(yawOffset(deg),pitchOffset(deg)))
    AprilTagFrontLeft = (
        (13.153, 12.972, 9.014),
        (10, -55.5),
        "Apriltag_FrontLeft_Camera",
    )
    AprilTagFrontRight = (
        (13.153, -12.972, 9.014),
        (-10, -55.5),
        "Apriltag_FrontRight_Camera",
    )
    AprilTagRearLeft = ((-13.153, 12.972, 9.014), (180, 0), "Apriltag_RearLeft_Camera")
    AprilTagRearRight = (
        (-13.153, -12.972, 9.014),
        (180, 0),
        "Apriltag_RearRight_Camera",
    )


class ATCameraExtrinsics2025(ATCameraExtrinsics, Enum):
    #   {PositionName} = ((offsetX(in),offsetY(in),offsetZ(in)),(yawOffset(deg),pitchOffset(deg)))
    AprilTagFrontLeft = ((10.14, 6.535, 6.7), (0, -21), "Apriltag_FrontLeft_Camera")
    AprilTagFrontRight = ((10.14, -6.535, 6.7), (0, -21), "Apriltag_FrontRight_Camera")
    # AprilTagBack = ((-10.25,0,7),(180,-45),"Apriltag_Back_Camera")


class CameraIntrinsics:
    def __init__(
        self,
        hres_pix=-1,
        vres_pix=-1,
        hfov_rad=-1,
        vfov_rad=-1,
        focal_length_mm=-1,
        pixel_size_mm=-1,
        sensor_size_mm=-1,
        fx_pix=-1,
        fy_pix=-1,
        cx_pix=-1,
        cy_pix=-1,
    ):
        self.value = (
            (hres_pix, vres_pix),  # Resolution
            (hfov_rad, vfov_rad),  # FOV
            (focal_length_mm, pixel_size_mm, sensor_size_mm),  # Physical Constants
            (fx_pix, fy_pix),  # Calibrated Fx, Fy
            (cx_pix, cy_pix),  # Calibrated Cx, Cy
        )

    """
    Create camera intrinsics at runtime.\n
    WARNING, any unfilled values may cause errors down the line. Please override default values you know you need
    """

    def getHres(self) -> float:
        return self.value[0][0]

    def getVres(self) -> float:
        return self.value[0][1]

    def getHFovRad(self) -> float:
        return self.value[1][0]

    def getVFovRad(self) -> float:
        return self.value[1][1]

    def getFocalLengthMM(self) -> float:
        return self.value[2][0]

    def getPixelSizeMM(self) -> float:
        return self.value[2][1]

    def getSensorSizeMM(self) -> float:
        return self.value[2][2]

    def getFx(self) -> float:
        assert len(self.value) > 3
        return self.value[3][0]

    def getFy(self) -> float:
        assert len(self.value) > 3
        return self.value[3][1]

    def getCx(self) -> float:
        assert len(self.value) > 4
        return self.value[4][0]

    def getCy(self) -> float:
        assert len(self.value) > 4
        return self.value[4][1]


class CameraIntrinsicsPredefined:
    #                       res             fov                     physical constants
    #   {CameraName} = ((HRes(pixels),Vres(pixels)),(Hfov(rad),Vfov(rad)),(Focal Length(mm),PixelSize(mm),sensor size(mm)), (CalibratedFx(pixels),CalibratedFy(pixels)),(CalibratedCx(pixels),CalibratedCy(pixels)))
    OV9782COLOR = CameraIntrinsics(
        640,
        480,  # Resolution
        1.22173,
        -1,  # FOV
        1.745,
        0.003,
        6.3,  # Physical Constants
        541.637,
        542.563,  # Calibrated Fx, Fy
        346.66661258567217,
        232.5032948773164,  # Calibrated Cx, Cy
    )

    SIMULATIONCOLOR = CameraIntrinsics(
        640,
        480,  # Resolution
        1.22173,
        0.9671,  # FOV
        1.745,
        0.003,
        6.3,  # Physical Constants
        609.34,
        457,  # Calibrated Fx, Fy
        320,
        240,  # Calibrated Cx, Cy
    )


class ObjectReferences(Enum):
    NOTE = (35.56, 14)  # cm , in
    BUMPERHEIGHT = (12.7, 5)  # cm, in
    ALGAEDIAMETER = (40.64, 16)  # cm in
    ALGAEDIAMETER = (40.64, 16)  # cm in

    def getMeasurementCm(self) -> float:
        return self.value[0]

    def getMeasurementIn(self) -> float:
        return self.value[1]


class ConfigConstants:
    confThreshold = 0.7


class KalmanConstants:
    Q = np.eye(4) * 0.01  # Process noise covariance
    R = np.eye(2) * 0.01  # Measurement noise covariance


class CameraIdOffsets(Enum):
    # jump of 30
    FRONTLEFT = 0
    FRONTRIGHT = 30
    REARLEFT = 60
    REARRIGHT = 90
    DEPTHLEFT = 120
    DEPTHRIGHT = 150

    def getIdOffset(self) -> int:
        return self.value


class Landmarks(Enum):
    BlueTopCoralStationLeftLoad = (1.608, 7.26, -54)
    BlueTopCoralStationMiddleLoad = (1.225, 7, -54)
    BlueTopCoralStationRightLoad = (0.811, 6.7, -54)
    BlueBottomCoralStationLeftLoad = (0.811, 1.35, 54)
    BlueBottomCoralStationMiddleLoad = (1.225, 1.031, 54)
    BlueBottomCoralStationRightLoad = (1.608, 0.764, 54)
    BlueProcessorScoringLocation = (11.56, 7.51, -90)

    BlueCloseReefFace = (3.158, 4.026, 0)
    BlueCloseRightReefFace = (3.829, 2.880, 60)
    BlueCloseLeftReefFace = (3.829, 5.180, -60)
    BlueBackLeftReefFace = (5.150, 5.180, -120)
    BlueBackReefFace = (5.821, 5.821, -180)
    BlueBackRightReefFace = (5.150, 2.880, 120)

    def get_cm(self) -> tuple[float, float]:
        """Convert the x and y coordinates from meters to centimeters."""
        x_m, y_m, _ = self.value
        return x_m * 100, y_m * 100

    def get_m(self):
        """Convert the x and y coordinates from meters to centimeters."""
        x_m, y_m, _ = self.value
        return x_m, y_m

    def get_angle(self) -> float:
        """Retrieve the rotation angle in degrees."""
        return self.value[2]


class MapConstants(Enum):
    GameObjectAcceleration = 0  # probably?
    RobotMaxVelocity = 300  # cm/s
    RobotAcceleration = 150  # cm/s^2 this is probably inaccurate?
    fieldWidth = 1755  # 54' 3" in cm
    fieldHeight = 805  # 26' 3" in cm
    res = 5  # cm
    robotWidth = 75  # cm
    robotHeight = 75  # cm assuming square robot with max frame perimiter of 300
    gameObjectWidth = 35  # cm
    gameObjectHeight = 35  # cm
    gameObjectHeight = 35  # cm

    mapObstacles = []  # todo define these
    reefRadius = 83.185  # cm
    b_reef_center = (411.48, 365.76)  # cm
    r_reef_center = (1234.44, 365.76)  # cm
    reefRadius = 83.185  # cm
    b_reef_center = (411.48, 365.76)  # cm
    r_reef_center = (1234.44, 365.76)  # cm
    reef_post_radius = 1.5875

    coral_inner_diameter = 10.16  # cm
    coral_outer_diameter = 11.43  # cm
    coral_inner_diameter = 10.16  # cm
    coral_outer_diameter = 11.43  # cm

    coral_width = 30.16  # cm
    coral_width = 30.16  # cm

    def getCM(self):
        return self.value


class LabelingConstants(Enum):
    MAXFRAMESNOTSEEN = 15


# todo consolidate camera info into one central enum
# class CAMERA(Enum):


def getCameraIfOffset(cameraName: str) -> CameraIdOffsets | None:
    for cameraIdOffset in CameraIdOffsets:
        if cameraIdOffset.name == cameraName:
            return cameraIdOffset

    return None


def getCameraExtrinsics(cameraName):
    for cameraExtrinsic in ColorCameraExtrinsics2024:
        if cameraExtrinsic.name == cameraName:
            return cameraExtrinsic

    return None


def getCameraName(cameraId: int) -> Any | None:
    if cameraId == 0:
        return ...

    return None


def getCameraValues(
    cameraName: str,
) -> tuple[CameraIntrinsics, CameraExtrinsics | None, CameraIdOffsets | None]:
    return (
        CameraIntrinsicsPredefined.OV9782COLOR,
        getCameraExtrinsics(cameraName),
        getCameraIfOffset(cameraName),
    )
