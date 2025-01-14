from enum import Enum
import math

import numpy as np


class CameraExtrinsics(Enum):
    #   {PositionName} = ((offsetX(in),offsetY(in),offsetZ(in)),(yawOffset(deg),pitchOffset(deg)))
    FRONTLEFT = ((13.779, 13.887, 10.744), (80, -3))
    FRONTRIGHT = ((13.779, -13.887, 10.744), (280, -3))
    REARLEFT = ((-13.116, 12.853, 10.52), (215, -3.77))
    REARRIGHT = ((-13.116, -12.853, 10.52), (145, -3.77))
    DEPTHLEFT = ((13.018, 2.548, 19.743), (24, -17))
    DEPTHRIGHT = ((13.018, -2.548, 19.743), (-24, -17))
    NONE = ((0, 0, 0), (0, 0))

    def getOffsetXIN(self):
        return self.value[0][0]
    
    def getOffsetXCM(self):
        return self.value[0][0]*2.54

    def getOffsetYIN(self):
        return self.value[0][1]
    
    def getOffsetYCM(self):
        return self.value[0][1]*2.54

    def getOffsetZIN(self):
        return self.value[0][2]
    
    def getOffsetZCM(self):
        return self.value[0][1]*2.54

    def getYawOffset(self):
        return self.value[1][0]

    def getPitchOffset(self):
        return self.value[1][1]

    def getYawOffsetAsRadians(self):
        return math.radians(self.value[1][0])

    def getPitchOffsetAsRadians(self):
        return math.radians(self.value[1][1])


class CameraIntrinsics(Enum):
    #                       res             fov                     physical constants
    #   {CameraName} = ((HRes(pixels),Vres(pixels)),(Hfov(rad),Vfov(rad)),(Focal Length(mm),PixelSize(mm),sensor size(mm)), (CalibratedFx(pixels),CalibratedFy(pixels)),(CalibratedCx(pixels),CalibratedCy(pixels)))
    OV9782COLOR = (
        (640, 480),
        (1.22173, -1),
        (1.745, 0.003, 6.3),
        (541.637, 542.563),
        (346.66661258567217, 232.5032948773164),
    )
    OV9281BaW = ((640, 480), (1.22173, -1), (-1, 0.003, 6.3))
    OAKDLITE = ((1920, 1080), (1.418953, -1), (3.37, 0.00112, 8.193))
    SIMULATIONCOLOR = (
        (640, 480),
        (1.22173, 0.9671),
        (1.745, 0.003, 6.3),
        (609.34, 457),        
        (320, 240),
    )

    def getHres(self):
        return self.value[0][0]

    def getVres(self):
        return self.value[0][1]

    def getHFov(self):
        return self.value[1][0]

    def getVFov(self):
        return self.value[1][1]

    def getFocalLength(self):
        return self.value[2][0]

    def getPixelSize(self):
        return self.value[2][1]

    def getSensorSize(self):
        return self.value[2][2]

    def getFx(self):
        return self.value[3][0]

    def getFy(self):
        return self.value[3][1]

    def getCx(self):
        return self.value[4][0]

    def getCy(self):
        return self.value[4][1]


class ObjectReferences(Enum):
    NOTE = (35.56, 14)  # cm , in
    BUMPERHEIGHT = (12.7, 5)  # cm, in

    def getMeasurementCm(self):
        return self.value[0]

    def getMeasurementIn(self):
        return self.value[1]


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

    def getIdOffset(self):
        return self.value


class MapConstants(Enum):
    GameObjectAcceleration = 0  # probably?
    RobotMaxVelocity = 300  # cm/s
    RobotAcceleration = 150  # cm/s^2 this is probably inaccurate?
    fieldWidth = 1653  # 54' 3" in cm
    fieldHeight = 800  # 26' 3" in cm
    res = 5  # cm
    robotWidth = 75  # cm
    robotHeight = 75  # cm assuming square robot with max frame perimiter of 300
    gameObjectWidth = 35  # cm
    gameObjectHeight = 35  # cm circular note

    mapObstacles = []  # todo define these
    chainsAtMinPoint = 71.755 # cm

    def getCM(self):
        return self.value
    def getIn(self):
        return self.value / 2.54


class LabelingConstants(Enum):
    MAXFRAMESNOTSEEN = 15

class UnitMode(Enum):
    CM = "cm"
    IN = "inch"

# todo consolidate camera info into one central enum
# class CAMERA(Enum):


def getCameraIfOffset(cameraName):
    for cameraIdOffset in CameraIdOffsets:
        if cameraIdOffset.name == cameraName:
            return cameraIdOffset


def getCameraExtrinsic(cameraName):
    for cameraExtrinsic in CameraExtrinsics:
        if cameraExtrinsic.name == cameraName:
            return cameraExtrinsic


def getCameraName(cameraId):
    if cameraId == 0:
        return ...


def getCameraValues(cameraName):
    return (
        CameraIntrinsics.OV9782COLOR,
        getCameraExtrinsic(cameraName),
        getCameraIfOffset(cameraName),
    )
