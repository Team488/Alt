from tools.Constants import CameraExtrinsics
import math
import numpy as np

def transformWithYaw(posVector,yaw):
    # print(f"{posVector=} {yaw=}")
    yawTransform = np.array(
            [
                [math.cos(yaw), -math.sin(yaw), 0],
                [math.sin(yaw), math.cos(yaw), 0],
                [0, 0, 1],
            ]
        )
    return yawTransform @ posVector


class CameraToRobotTranslator:
    def __init__(self) -> None:
        pass

    def turnCameraCoordinatesIntoRobotCoordinates(
        self, relativeX, relativeY, cameraExtrinsics: CameraExtrinsics
    ) -> tuple[float, float, float]:
        dx = cameraExtrinsics.getOffsetX()
        dy = cameraExtrinsics.getOffsetY()
        dz = cameraExtrinsics.getOffsetZ()
        yaw = cameraExtrinsics.getYawOffsetAsRadians()
        pitch = cameraExtrinsics.getPitchOffsetAsRadians()
        # print(f"camera offset: [{dx}, {dy}, {dz}] pitch: {yaw} yaw: {pitch}")

        noteVector = np.array(
            [[relativeX], [relativeY], [0]]
        )  # z is 0 because we are not factoring in target height relative to camera for now

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
        rotationMatrix = yawTransform @ pitchTransform

        # Undo the camera offsets from rotation
        rotatedNoteVector = rotationMatrix @ noteVector
        # print(f"After rotation: x {rotatedNoteVector[0]} y {rotatedNoteVector[1]}")

        # Define translation
        translationVector = np.array([[dx], [dy], [dz]])

        robotRelativeNoteVector = np.add(rotatedNoteVector, translationVector)

        finalX = robotRelativeNoteVector[0][0]
        finalY = robotRelativeNoteVector[1][0]
        finalZ = robotRelativeNoteVector[2][0]

        # print(f"After rotation and translation: x {robotRelativeNoteVector[0]} y {robotRelativeNoteVector[1]}")

        return (finalX, finalY, finalZ)
