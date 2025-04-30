from enum import Enum
import math
from Alt.Core.Units import Types, Conversions
import numpy as np
from scipy.spatial.transform import Rotation

class CameraExtrinsics(Enum):
    #   {PositionName} = ((offsetX(in),offsetY(in),offsetZ(in)),(yawOffset(deg),pitchOffset(deg)))
    # Values will be added as enum members when subclassing

    @staticmethod
    def getDefaultLengthType() -> Types.Length:
        return Types.Length.IN

    @staticmethod
    def getDefaultRotationType() -> Types.Rotation:
        return Types.Rotation.Deg

    def getOffsetXIN(self) -> float:
        return self.value[0][0]

    def getOffsetXCM(self) -> float:
        return self.value[0][0] * 2.54

    def getOffsetYIN(self) -> float:
        return self.value[0][1]

    def getOffsetYCM(self) -> float:
        return self.value[0][1] * 2.54

    def getOffsetZIN(self) -> float:
        return self.value[0][2]

    def getOffsetZCM(self) -> float:
        return self.value[0][2] * 2.54  # Fixed typo (was using Y instead of Z)

    def getYawOffset(self) -> float:
        return self.value[1][0]

    def getPitchOffset(self) -> float:
        return self.value[1][1]

    def getYawOffsetAsRadians(self) -> float:
        return math.radians(self.value[1][0])

    def getPitchOffsetAsRadians(self) -> float:
        return math.radians(self.value[1][1])

    def get4x4AffineMatrix(
        self, lengthType: Types.Length = Types.Length.CM
    ) -> np.ndarray:
        """Returns a 4x4 affine transformation matrix for the camera extrinsics"""

        x_in, y_in, z_in = self.value[0]
        yaw, pitch = map(math.radians, self.value[1])  # Convert degrees to radians

        # Handle different possible return types from convertLength
        position_result = Conversions.convertLength(
            (x_in, y_in, z_in), CameraExtrinsics.getDefaultLengthType(), lengthType
        )

        # Ensure we have a 3D position
        if isinstance(position_result, tuple) and len(position_result) == 3:
            x, y, z = position_result
        else:
            # Default to zeros if conversion fails
            x, y, z = 0.0, 0.0, 0.0

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
    DEPTH_REAR_LEFT = ((0, 0, 0), (45.0, 10.0))
    DEPTH_REAR_RIGHT = ((0, 0, 0), (45.0, 10.0))


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
