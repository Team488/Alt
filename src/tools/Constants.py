from enum import Enum
import math


class CameraExtrinsics(Enum):
    #   {PositionName} = ((offsetX,offsetY,offsetZ),(yawOffset,pitchOffset))
    FRONTLEFT = ((13.779, 13.887, 10.744), (80, -3))
    FRONTRIGHT = ((13.779, -13.887, 10.744), (280, -3))
    REARLEFT = ((-13.116, 12.853, 10.52), (215, -3.77))
    REARRIGHT = ((-13.116, -12.853, 10.52), (145, -3.77))
    DEPTHLEFT = ((13.018, 2.548, 19.743), (24, -17))
    DEPTHRIGHT = ((13.018, -2.548, 19.743), (-24, -17))

    def getOffsetX(self):
        return self.value[0][0]

    def getOffsetY(self):
        return self.value[0][1]

    def getOffsetZ(self):
        return self.value[0][2]

    def getYawOffset(self):
        return self.value[1][0]

    def getPitchOffset(self):
        return self.value[1][1]

    def getYawOffsetAsRadians(self):
        return math.radians(self.value[1][0])

    def getPitchOffsetAsRadians(self):
        return math.radians(self.value[1][1])


class CameraIntrinsics(Enum):
    #   {CameraName} = ((HRes,Vres),(Hfov(rad),Vfov(rad)),(Focal Length(mm),PixelSize(mm)))
    OV9782COLOR = ((640, 480), (1.22173, -1), (2.88, 0.003))
    OV9281BaW = ((640, 480), (1.22173, -1), (-1, 0.003))
    OAKDLITE = ((1920, 1080), (1.418953, -1), (3.37, 0.00112))

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


class ObjectReferences(Enum):
    NOTE = 14  # inches
    BUMPERHEIGHT = 5  # inches

    def getMeasurement(self):
        return self.value
