from tools.Constants import CameraExtrinsics
import math
from typing import Tuple, Union, List, Any, cast
import numpy as np

Vector = Union[np.ndarray, List[Union[float, int]], Tuple[Union[float, int], ...]]


def transformWithYaw(posVector: Vector, yaw: float) -> np.ndarray:
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
    
    # Apply the transformation
    return yawTransform @ posVector


class CameraToRobotTranslator:
    """
    Translates coordinates from camera frame to robot frame,
    accounting for camera position and orientation
    """
    
    def __init__(self) -> None:
        """Initialize the translator"""
        pass

    def turnCameraCoordinatesIntoRobotCoordinates(
        self, relativeX: float, relativeY: float, cameraExtrinsics: CameraExtrinsics
    ) -> Tuple[float, float, float]:
        """
        Transform coordinates from camera frame to robot frame
        
        Args:
            relativeX: X coordinate in camera frame (in centimeters)
            relativeY: Y coordinate in camera frame (in centimeters)
            cameraExtrinsics: Camera extrinsic parameters (position and orientation)
            
        Returns:
            A tuple of (x, y, z) coordinates in robot frame (in centimeters)
        """
        # Get camera position and orientation
        dx = cameraExtrinsics.getOffsetXCM()
        dy = cameraExtrinsics.getOffsetYCM()
        dz = cameraExtrinsics.getOffsetZCM()
        yaw = cameraExtrinsics.getYawOffsetAsRadians()
        pitch = cameraExtrinsics.getPitchOffsetAsRadians()
        # print(f"camera offset: [{dx}, {dy}, {dz}] pitch: {yaw} yaw: {pitch}")

        # Create position vector (z is 0 because we are not factoring in 
        # target height relative to camera)
        noteVector = np.array(
            [[relativeX], [relativeY], [0]]
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
        rotatedNoteVector = rotationMatrix @ noteVector
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

        return (finalX, finalY, finalZ)
