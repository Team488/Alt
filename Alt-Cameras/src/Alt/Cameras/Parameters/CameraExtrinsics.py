import numpy as np
from scipy.spatial.transform import Rotation
from Alt.Core.Units import Types, Conversions

class CameraExtrinsics:
    def __init__(
        self, 
        offsetX : float, offsetY : float, offsetZ : float,
        yawOffset : float, pitchOffset : float, 
        translationUnits : Types.Length = Types.Length.IN,
        rotationUnits : Types.Rotation = Types.Rotation.Deg):

        # convert whatever input length units into inches
        self.offsetXIn, self.offsetYIn, self.offsetZIn = Conversions.convertLength((offsetX, offsetY, offsetZ), translationUnits, Types.Length.IN)
        # convert whatever input rotation units to degrees
        self.yawOffsetDeg, self.pitchOffsetDeg = Conversions.convertRotation((yawOffset, pitchOffset), rotationUnits, Types.Rotation.Deg)


    @staticmethod
    def getDefaultLengthType() -> Types.Length:
        return Types.Length.IN

    @staticmethod
    def getDefaultRotationType() -> Types.Rotation:
        return Types.Rotation.Deg

    def getOffsetX(self, units : Types.Length.IN) -> float:
        return Conversions.convertLength(self.offsetXIn, self.getDefaultLengthType(), units)

    def getOffsetY(self, units : Types.Length.IN) -> float:
        return Conversions.convertLength(self.offsetYIn, self.getDefaultLengthType(), units)

    def getOffsetZ(self, units : Types.Length.IN) -> float:
        return Conversions.convertLength(self.offsetZIn, self.getDefaultLengthType(), units)

    def getYawOffset(self, units : Types.Rotation.Deg) -> float:
        return Conversions.convertRotation(self.yawOffsetDeg, self.getDefaultRotationType(), units)

    def getPitchOffset(self, units : Types.Rotation.Deg) -> float:
        return Conversions.convertRotation(self.pitchOffsetDeg, self.getDefaultRotationType(), units)

    def get4x4AffineMatrix(
        self, lengthUnits: Types.Length = Types.Length.CM
    ) -> np.ndarray:
        """Returns a 4x4 affine transformation matrix for the camera extrinsics"""

        rotation_matrix = Rotation.from_euler(
            "zy", [self.getYawOffset(), self.getPitchOffset()], degrees=True
        ).as_matrix()

        # Construct the 4x4 transformation matrix
        affine_matrix = np.eye(4)
        affine_matrix[:3, :3] = rotation_matrix
        affine_matrix[:3, 3] = [
            self.getOffsetX(lengthUnits), 
            self.getOffsetY(lengthUnits), 
            self.getOffsetZ(lengthUnits)
        ]  

        return affine_matrix


