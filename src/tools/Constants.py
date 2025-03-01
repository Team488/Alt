from abc import abstractmethod
from enum import Enum
import json
from typing import Union, Any
from tools import UnitConversion, Units
import math
import cv2
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


class Label(Enum):
    # name, w,h (cm)
    ROBOT = ("robot", (75, 75))
    NOTE = ("note", (35, 35))
    ALGAE = ("algae", (41, 41))
    CORAL = ("coral", (30, 12))

    def getDefaultLengthType():
        return Units.LengthType.CM

    def __str__(self) -> str:
        return self.value[0]

    def getSize(self, lengthType: Units.LengthType):
        return UnitConversion.convertLength(
            self.getSizeCm(), self.getDefaultLengthType(), lengthType
        )

    def getSizeCm(self):
        return self.value[1]


class ModelType(Enum):
    ALCORO = (Label.ALGAE, Label.CORAL, Label.ROBOT)
    CORO = (Label.CORAL, Label.ROBOT)
    NORO = (Label.NOTE, Label.ROBOT)


class InferenceMode(Enum):
    ONNX2024 = (
        "assets/yolov5s_fp32.onnx",
        "yolov5s-onnx-fp32",
        (Label.ROBOT, Label.NOTE),
        2024,
        Backend.ONNX,
        YOLOTYPE.V5,
        ModelType.NORO,
    )
    ONNXSMALL2025 = (
        "assets/yolov11s_fp32.onnx",
        "yolov11s-onnx-small-fp32",
        (Label.ALGAE, Label.CORAL),
        2025,
        Backend.ONNX,
        YOLOTYPE.V11,
        ModelType.CORO,
    )
    ONNXMEDIUM2025 = (
        "assets/yolov11m_fp32.onnx",
        "yolov11m-onnx-medium-fp32",
        (Label.ALGAE, Label.CORAL),
        2025,
        Backend.ONNX,
        YOLOTYPE.V11,
        ModelType.CORO,
    )
    RKNN2024FP32 = (
        "assets/yolov5s_fp32.rknn",
        "yolov5s-rknn-fp32",
        (Label.ROBOT, Label.NOTE),
        2024,
        Backend.RKNN,
        YOLOTYPE.V5,
        ModelType.NORO,
    )
    RKNN2025INT8 = (
        "assets/yolov11s_int8.rknn",
        "yolov11s-rknn-int8",
        (Label.ALGAE, Label.CORAL),
        2025,
        Backend.RKNN,
        YOLOTYPE.V11,
        ModelType.CORO,
    )

    ULTRALYTICSSMALL2025 = (
        "assets/yolov11s_fp32.pt",
        "yolov11s-pytorch-small-fp32",
        (Label.ALGAE, Label.CORAL),
        2025,
        Backend.ULTRALYTICS,
        YOLOTYPE.V11,
        ModelType.CORO,
    )
    ULTRALYTICSMED2025 = (
        "assets/yolov11m_fp32.pt",
        "yolov11s-pytorch-medium-fp32",
        (Label.ALGAE, Label.CORAL),
        2025,
        Backend.ULTRALYTICS,
        YOLOTYPE.V11,
        ModelType.CORO,
    )
    ALCOROULTRALYTICSSMALL2025BAD = (
        (
            "assets/yolov8s_fp32_BADDD.pt",
            "verybad-yolov8s-pytorch-medium-fp32",
            (Label.ALGAE, Label.CORAL, Label.ROBOT),
            2025,
            Backend.ULTRALYTICS,
            YOLOTYPE.V8,
            ModelType.ALCORO,
        ),
    )
    ALCOROBEST2025 = (
        "assets/yolo11sBestTensorRT.engine",
        "yolov11s-best-tensorrt",
        (Label.ALGAE, Label.CORAL, Label.ROBOT),
        2025,
        Backend.ULTRALYTICS,
        YOLOTYPE.V11,
        ModelType.ALCORO,
    )

    # TORCH todo!

    def getModelPath(self) -> str:
        return self.value[0]

    def getName(self):
        return self.value[1]

    def getLabelsAsStr(self):
        return list(map(str, self.value[2]))

    def getLabels(self):
        return self.value[2]

    def getYear(self):
        return self.value[3]

    def getBackend(self):
        return self.value[4]

    def getYoloType(self):
        return self.value[5]

    def getModelType(self):
        return self.value[6]

    @classmethod
    def getFromName(cls, name: str, default: Any = None):
        for mode in cls:
            if mode.getName() == name:
                return mode
        return default

    @classmethod
    def assertModelType(
        cls, inferenceMode1: "InferenceMode", inferenceMode2: "InferenceMode"
    ):
        return inferenceMode1.getModelType() == inferenceMode2.getModelType()


class Object(Enum):
    ALGAE = "a"
    CORAL = "c"
    NOTE = "n"
    ROBOT = "r"


class CameraExtrinsics:
    #   {PositionName} = ((offsetX(in),offsetY(in),offsetZ(in)),(yawOffset(deg),pitchOffset(deg)))
    @staticmethod
    def getDefaultLengthType():
        return Units.LengthType.IN

    @staticmethod
    def getDefaultRotationType():
        return Units.RotationType.Deg

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

    def get4x4AffineMatrix(self, lengthType: Units.LengthType = Units.LengthType.CM):
        """Returns a 4x4 affine transformation matrix for the camera extrinsics"""

        x_in, y_in, z_in = self.value[0]
        yaw, pitch = map(math.radians, self.value[1])  # Convert degrees to radians

        x, y, z = UnitConversion.convertLength(
            (x_in, y_in, z_in), CameraExtrinsics.getDefaultLengthType(), lengthType
        )

        # Create rotation matrix (assuming yaw around Z, pitch around Y)
        rotation_matrix = Rotation.from_euler(
            "zy", [yaw, pitch], degrees=False
        ).as_matrix()

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
        hres_pix: int = -1,
        vres_pix: int = -1,
        hfov_rad: float = -1,
        vfov_rad: Union[float, int] = -1,
        focal_length_mm: float = -1,
        pixel_size_mm: float = -1,
        sensor_size_mm: float = -1,
        fx_pix: float = -1,
        fy_pix: Union[int, float] = -1,
        cx_pix: Union[int, float] = -1,
        cy_pix: Union[int, float] = -1,
    ) -> None:
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

    @staticmethod
    def getHfov(cameraIntr: "CameraIntrinsics", radians: bool = True):
        hres = cameraIntr.getHres()
        fx = cameraIntr.getFx()

        rad = 2 * math.atan(hres / (2 * fx))
        if radians:
            return rad
        return math.degrees(rad)

    @staticmethod
    def getVfov(cameraIntr: "CameraIntrinsics", radians: bool = True):
        vres = cameraIntr.getVres()
        fy = cameraIntr.getFx()

        rad = 2 * math.atan(vres / (2 * fy))
        if radians:
            return rad
        return math.degrees(rad)

    @staticmethod
    def fromPhotonConfig(photonConfigPath):
        try:
            with open(photonConfigPath) as PV_config:
                data = json.load(PV_config)

                cameraIntrinsics = data["cameraIntrinsics"]["data"]
                fx = cameraIntrinsics[0]
                fy = cameraIntrinsics[4]
                cx = cameraIntrinsics[2]
                cy = cameraIntrinsics[5]

                width = int(data["resolution"]["width"])
                height = int(data["resolution"]["height"])

                return CameraIntrinsics(
                    hres_pix=width,
                    vres_pix=height,
                    fx_pix=fx,
                    fy_pix=fy,
                    cx_pix=cx,
                    cy_pix=cy,
                )

        except Exception as e:
            print(f"Failed to open config! {e}")
            return None

    @staticmethod
    def fromCustomConfig(customConfigPath):
        try:
            with open(customConfigPath) as custom_config:
                data = json.load(custom_config)

                cameraIntrinsics = data["CameraMatrix"]
                fx = cameraIntrinsics[0][0]
                fy = cameraIntrinsics[1][1]
                cx = cameraIntrinsics[0][2]
                cy = cameraIntrinsics[1][2]

                width = int(data["resolution"]["width"])
                height = int(data["resolution"]["height"])

                return CameraIntrinsics(
                    hres_pix=width,
                    vres_pix=height,
                    fx_pix=fx,
                    fy_pix=fy,
                    cx_pix=cx,
                    cy_pix=cy,
                )

        except Exception as e:
            print(f"Failed to open config! {e}")
            return None

    @staticmethod
    def setCapRes(cameraIntrinsics: "CameraIntrinsics", cap: cv2.VideoCapture):
        cap.set(cv2.CAP_PROP_FRAME_WIDTH, cameraIntrinsics.getHres())
        cap.set(cv2.CAP_PROP_FRAME_HEIGHT, cameraIntrinsics.getVres())
        return cap


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
        604,
        414,  # Calibrated Fx, Fy
        320,
        240,  # Calibrated Cx, Cy
    )


class OAKDLITEResolution(Enum):
    OAK4K = (3840, 2160, 30)
    OAK1080P = (1920, 1080, 60)

    @property
    def fps(self):
        return self.value[2]

    @property
    def w(self):
        return self.value[0]

    @property
    def h(self):
        return self.value[1]


class D435IResolution(Enum):
    RS720P = (1280, 720, 30)
    RS480P = (640, 480, 60)

    @property
    def fps(self):
        return self.value[2]

    @property
    def w(self):
        return self.value[0]

    @property
    def h(self):
        return self.value[1]


class CommonVideos(Enum):
    ReefscapeCompilation = "assets/reefscapevid.mp4"
    Comp2024Clip = "assets/video12qual25clipped.mp4"

    @property
    def path(self):
        return self.value


class SimulationEndpoints(Enum):
    FRONTRIGHTSIM = "http://localhost:3000/Robot_FrontRight%20Camera?dummy=param.mjpg"
    FRONTLEFTSIM = "http://localhost:3000/Robot_FrontLeft%20Camera?dummy=param.mjpg"
    REARRIGHTSIM = "http://localhost:3000/Robot_RearRight%20Camera?dummy=param.mjpg"
    REARLEFTSIM = "http://localhost:3000/Robot_RearLeft%20Camera?dummy=param.mjpg"

    @property
    def path(self):
        return self.value


class ObjectReferences(Enum):
    NOTE = (35.56, 14)  # cm , in
    BUMPERHEIGHT = (12.7, 5)  # cm, in
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


class CameraIdOffsets2024(Enum):
    # jump of 30
    FRONTLEFT = 0
    FRONTRIGHT = 30
    REARLEFT = 60
    REARRIGHT = 90
    DEPTHLEFT = 120
    DEPTHRIGHT = 150

    def getIdOffset(self) -> int:
        return self.value


class CameraIdOffsets2025(Enum):
    # jump of 30
    FRONTLEFT = 0
    FRONTRIGHT = 30
    BACK = 60
    DEPTHLEFT = 120
    DEPTHRIGHT = 150

    def getIdOffset(self) -> int:
        return self.value


class TEAM(Enum):
    RED = "red"
    BLUE = "blue"


class ATLocations(Enum):
    """
    AprilTag locations with ID, (x, y, z) coordinates in inches, and (yaw, pitch) rotations in degrees.
    """

    @staticmethod
    def getDefaultLengthType():
        return Units.LengthType.IN

    @staticmethod
    def getDefaultRotationType():
        return Units.RotationType.Deg

    TAG_1 = ((1), (657.37, 25.80, 58.50), (126, 0), None, None)
    TAG_2 = ((2), (657.37, 291.20, 58.50), (234, 0), None, None)
    TAG_3 = ((3), (455.15, 317.15, 51.25), (270, 0), None, None)
    TAG_4 = ((4), (365.20, 241.64, 73.54), (0, 30), None, None)
    TAG_5 = ((5), (365.20, 75.39, 73.54), (0, 30), None, None)
    TAG_6 = ((6), (530.49, 130.17, 12.13), (300, 0), TEAM.RED, 1)
    TAG_7 = ((7), (546.87, 158.50, 12.13), (0, 0), TEAM.RED, 2)
    TAG_8 = ((8), (530.49, 186.83, 12.13), (60, 0), TEAM.RED, 1)
    TAG_9 = ((9), (497.77, 186.83, 12.13), (120, 0), TEAM.RED, 2)
    TAG_10 = ((10), (481.39, 158.50, 12.13), (180, 0), TEAM.RED, 1)
    TAG_11 = ((11), (497.77, 130.17, 12.13), (240, 0), TEAM.RED, 2)
    TAG_12 = ((12), (33.51, 25.80, 58.50), (54, 0), None, None)
    TAG_13 = ((13), (33.51, 291.20, 58.50), (306, 0), None, None)
    TAG_14 = ((14), (325.68, 241.64, 73.54), (180, 30), None, None)
    TAG_15 = ((15), (325.68, 75.39, 73.54), (180, 30), None, None)
    TAG_16 = ((16), (235.73, -0.15, 51.25), (90, 0), None, None)
    TAG_17 = ((17), (160.39, 130.17, 12.13), (240, 0), TEAM.BLUE, 1)
    TAG_18 = ((18), (144.00, 158.50, 12.13), (180, 0), TEAM.BLUE, 2)
    TAG_19 = ((19), (160.39, 186.83, 12.13), (120, 0), TEAM.BLUE, 1)
    TAG_20 = ((20), (193.10, 186.83, 12.13), (60, 0), TEAM.BLUE, 2)
    TAG_21 = ((21), (209.49, 158.50, 12.13), (0, 0), TEAM.BLUE, 1)
    TAG_22 = ((22), (193.10, 130.17, 12.13), (300, 0), TEAM.BLUE, 2)

    @property
    def id(self):
        return self.value[0]

    @property
    def position(self):
        return self.value[1]

    @property
    def rotation(self):
        return self.value[2]

    @property
    def team(self):
        return self.value[3]

    @property
    def blockingAlgaeLevel(self):
        return self.value[4]

    @classmethod
    def get_by_id(cls, tag_id):
        """Retrieve an ATLocation by its ID."""
        for tag in cls:
            if tag.id == tag_id:
                return tag
        return None

    @classmethod
    def get_pose_by_id(
        cls,
        tag_id,
        length: Units.LengthType = Units.LengthType.CM,
        rotation: Units.RotationType = Units.RotationType.Rad,
    ):
        """Retrieve the position and rotation for a given tag ID."""
        tag = cls.get_by_id(tag_id)

        if tag is None:
            return None

        position = UnitConversion.convertLength(
            tag.position, cls.getDefaultLengthType(), length
        )

        rotation = UnitConversion.convertRotation(
            tag.rotation, cls.getDefaultRotationType(), rotation
        )

        return position, rotation

    @classmethod
    def getPoseAfflineMatrix(
        cls, tag_id, units: Units.LengthType = Units.LengthType.CM
    ):
        pose = cls.get_pose_by_id(tag_id, length=units)
        if pose is None:
            return None

        translation, rotation = pose
        rotMatrix = Rotation.from_euler("ZY", rotation, degrees=False).as_matrix()

        m = np.eye(4)
        m[:3, :3] = rotMatrix
        m[:3, 3] = translation
        return m

    @classmethod
    def getReefBasedIds(cls, team: TEAM = None) -> list[int]:
        if not team:
            return ATLocations.getReefBasedIds(TEAM.BLUE) + ATLocations.getReefBasedIds(
                TEAM.RED
            )

        ids = []
        for tag in cls:
            if tag.team == team:
                ids.append(tag.id)

        return ids

    @classmethod
    def getAlgaeLevel(cls, atId):
        tag = cls.get_by_id(atId)

        if tag is None:
            return None

        return tag.blockingAlgaeLevel

    @classmethod
    def getBlockedBranchIdxs(cls, atId):
        level = cls.getAlgaeLevel(atId)

        if level is None:
            return None

        if level == 1:
            return 0, 1, 2, 3
        if level == 2:
            return 2, 3, 4, 5


class ReefBranches(Enum):
    @staticmethod
    def getDefaultLengthType():
        return Units.LengthType.IN

    L2L = (0, "L2-L", np.array([-6.756, -19.707, 2.608]))
    L2R = (1, "L2-R", np.array([6.754, -19.707, 2.563]))
    L3L = (2, "L3-L", np.array([-6.639, -35.606, 2.628]))
    L3R = (3, "L3-R", np.array([6.637, -35.606, 2.583]))
    L4L = (4, "L4-L", np.array([-6.470, -58.4175, 0.921]))
    L4R = (5, "L4-R", np.array([6.468, -58.4175, 0.876]))

    @property
    def branchid(self):
        return self[0]

    @property
    def branchname(self):
        return self[1]

    def getAprilTagOffset(self, units: Units.LengthType = Units.LengthType.CM):
        return UnitConversion.convertLength(self[2], self.getDefaultLengthType(), units)

    @classmethod
    def getByID(cls, branchid: int):
        for branch in cls:
            if branch.branchid == branchid:
                return branch

        return None


class Landmarks(Enum):
    # in meters
    # NOT CORRECT VALUES
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
    @staticmethod
    def getDefaultLengthType():
        return Units.LengthType.CM

    @staticmethod
    def getDefaultRotationType():
        return Units.RotationType.Deg

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
    mapObstacles = []

    b_reef_center = (448.93, 402.59)  # cm
    r_reef_center = (1305.8902, 402.59)  # cm
    reefRadius = 83.185  # cm

    coral_inner_diameter = 10.16  # cm
    coral_outer_diameter = 11.43  # cm

    coral_width = 30.16  # cm

    def getCM(self) -> float:
        return self.value

    def getLength(
        self, lengthType: Units.LengthType = Units.LengthType.CM
    ) -> Union[tuple[float], float]:
        return UnitConversion.convertLength(
            self.getCM(), fromType=self.getDefaultLengthType(), toType=lengthType
        )


class LabelingConstants(Enum):
    MAXFRAMESNOTSEEN = 60  # around 2-3 sec


# todo consolidate camera info into one central enum
# class CAMERA(Enum):


def getCameraIfOffset2024(cameraName: str):
    for cameraIdOffset in CameraIdOffsets2024:
        if cameraIdOffset.name == cameraName:
            return cameraIdOffset

    return None


def getCameraExtrinsics2024(cameraName):
    for cameraExtrinsic in ColorCameraExtrinsics2024:
        if cameraExtrinsic.name == cameraName:
            return cameraExtrinsic

    return None


def getCameraValues2024(
    cameraName: str,
) -> tuple[CameraIntrinsics, CameraExtrinsics, CameraIdOffsets2024]:
    return (
        CameraIntrinsicsPredefined.OV9782COLOR,
        getCameraExtrinsics2024(cameraName),
        getCameraIfOffset2024(cameraName),
    )


def getCameraIfOffset2025(cameraName: str):
    for cameraIdOffset in CameraIdOffsets2025:
        if cameraIdOffset.name == cameraName:
            return cameraIdOffset

    return None


def getCameraExtrinsics2025(cameraName):
    for cameraExtrinsic in ColorCameraExtrinsics2025:
        if cameraExtrinsic.name == cameraName:
            return cameraExtrinsic

    return None


def getCameraValues2024(
    cameraName: str,
) -> tuple[CameraIntrinsics, CameraExtrinsics, CameraIdOffsets2024]:
    return (
        CameraIntrinsicsPredefined.OV9782COLOR,
        getCameraExtrinsics2025(cameraName),
        getCameraIfOffset2025(cameraName),
    )
