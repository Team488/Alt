import math
import numpy as np

from Alt.Core.Units.Poses import Transform3d
from Alt.Cameras.Parameters.CameraExtrinsics import CameraExtrinsics


def transformWithYaw(position: Transform3d, yaw: float) -> Transform3d:
    """
    Apply a yaw rotation to a position vector
    
    Args:
        posVector: Position vector to transform (shape must be compatible with the yaw transform matrix)
        yaw: Yaw angle in radians
        
    Returns:
        Transformed position vector after applying yaw rotation
    """
    # Create the yaw rotation matrix
    yawTransform = np.array(
        [
            [math.cos(yaw), -math.sin(yaw), 0],
            [math.sin(yaw), math.cos(yaw), 0],
            [0, 0, 1],
        ]
    )

    posVector = np.array[position.x, position.y, position.z]
    
    # Apply the transformation
    resultT = yawTransform @ posVector

    return Transform3d(resultT[0], resultT[1], resultT[2])


class CameraToRobotTranslator:
    """
    Translates coordinates from camera frame to robot frame,
    accounting for camera position and orientation
    """
    
    def __init__(self) -> None:
        """Initialize the translator"""
        pass

    def turnCameraCoordinatesIntoRobotCoordinates(
        self, relativeTransform : Transform3d, cameraExtrinsics: CameraExtrinsics
    ) -> Transform3d:
        """
        Transform coordinates from camera frame to robot frame
        
        Args:
            relativeTransform: Transform3d in camera frame
            cameraExtrinsics: Camera extrinsic parameters (position and orientation)
            
        Returns:
            A Transform3d coordinates in robot frame (in centimeters)
        """
        # Get camera position and orientation
        dx = cameraExtrinsics.getOffsetXCM()
        dy = cameraExtrinsics.getOffsetYCM()
        dz = cameraExtrinsics.getOffsetZCM()
        yaw = cameraExtrinsics.getYawOffsetAsRadians()
        pitch = cameraExtrinsics.getPitchOffsetAsRadians()
        # print(f"camera offset: [{dx}, {dy}, {dz}] pitch: {yaw} yaw: {pitch}")

        # TODO check relativeTransform units and change if not cm
        # if relativeTransform.units...

        relativeVector = np.array(
            [[relativeTransform.x], [relativeTransform.y], [relativeTransform.z]]
        )

        # Define rotation matrices
        yawTransform = np.array(
            [
                [math.cos(yaw), -math.sin(yaw), 0],
                [math.sin(yaw), math.cos(yaw), 0],
                [0, 0, 1],
            ]
        )

        pitchTransform = np.array(
            [
                [math.cos(pitch), 0, math.sin(pitch)],
                [0, 1, 0],
                [-math.sin(pitch), 0, math.cos(pitch)],
            ]
        )

        # Calculate the final transformation matrix
        rotationMatrix = pitchTransform @ yawTransform

        # Apply rotation to the position vector
        rotatedNoteVector = rotationMatrix @ relativeVector
        # print(f"After rotation: x {rotatedNoteVector[0]} y {rotatedNoteVector[1]}")

        # Define translation vector (camera position in robot frame)
        translationVector = np.array([[dx], [dy], [dz]])

        # Apply translation to get position in robot frame
        robotRelativeNoteVector = np.add(rotatedNoteVector, translationVector)

        # Extract the final coordinates
        finalX = float(robotRelativeNoteVector[0][0])
        finalY = float(robotRelativeNoteVector[1][0])
        finalZ = float(robotRelativeNoteVector[2][0])

        # print(f"After rotation and translation: x {robotRelativeNoteVector[0]} y {robotRelativeNoteVector[1]}")

        return Transform3d(finalX, finalY, finalZ)
