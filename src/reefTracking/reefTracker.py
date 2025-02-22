import time
import cv2
import json
import numpy as np
from typing import Dict
from wpimath.geometry import Transform3d
from reefTracking.aprilTagSolver import AprilTagSover
from reefTracking.aprilTagHelper import AprilTagLocal
from tools.Constants import CameraIntrinsics, CameraExtrinsics, ATCameraExtrinsics
from tools import Calculator, UnitConversion
from Core import getLogger


### CAD Offset:
### X = Downwards -> Right
### Y = Upwards -> Right
### Z = Upwards

# Measurement is in Inches

# CAD to tip of the rod. (MAX Distance)
cad_to_branch_offset = {
    0: np.array([-6.756, -19.707, 2.608]),      #"L2-L"
    1: np.array([6.754, -19.707, 2.563]),       #"L2-R"
    2: np.array([-6.639, -35.606, 2.628]),      #"L3-L"
    3: np.array([6.637, -35.606, 2.583]),       #"L3-R"
    4: np.array([-6.470, -58.4175, 0.921]),     #"L4-L" 
    5: np.array([6.468, -58.4175, 0.876]),      #"L4-R" 
}


# Convert to meters:
for branch, offset in cad_to_branch_offset.items():
    for i in range(len(offset)):
        offset[i] *= 0.0254

# CAD to Center of Coral
""""
cad_to_branch_offset = {
    "L2-L" : np.array([-6.470, -12.854, 9.00]),
    "L2-R" : np.array([6.468, -12.833, 9.00]),
    "L3-L" : np.array([-6.470, -23.503, 16.457]),
    "L3-R" : np.array([6.468, -23.482, 16.442]),
    "L4-L" : np.array([-6.470, -58.4175, 0.921]),
    "L4-R" : np.array([6.468, -58.4175, 0.876])
}
"""
### Camera AT Coordinate System:
#   X is LEFT -> Right  [-inf, inf]
#   Y is TOP -> Down    [-inf, inf]
#   Z is DEPTH AWAY     [0, inf]


zoffset = 3  # in
widthOffset = 6  # in                                                                   #               ↖  (z)
heightOffset = 10  # in                                                                 #                (3)
heightClearence = 0.5
depthOffset = 4  # in                                                             #                  \
reefBoxOffsetsFRONT = [  # in to m                                                       #                   \
    np.array(
        [widthOffset / 2 * 0.0254, -heightClearence * 0.0254, 0]
    ),  # (1)  (x) <(1)------o
    np.array(
        [-widthOffset / 2 * 0.0254, -heightClearence * 0.0254, 0]
    ),  # (2)                |
    np.array(
        [-widthOffset / 2 * 0.0254, heightOffset * 0.0254, 0]
    ),  # (2)                |
    np.array(
        [widthOffset / 2 * 0.0254, heightOffset * 0.0254, 0]
    ),  # (2)                |
    # np.array([-widthOffset / 2 * 0.0254, heightClearence * 0.0254, zoffset* 0.0254]),  # (3)               (2)
]
reefBoxOffsetsLEFT = [  # in to m
    np.array(
        [widthOffset / 2 * 0.0254, -heightClearence * 0.0254, depthOffset * 0.0254]
    ),  # top left
    np.array([widthOffset / 2 * 0.0254, -heightClearence * 0.0254, 0]),  # top right
    np.array([widthOffset / 2 * 0.0254, heightOffset * 0.0254, 0]),  # bottom right
    np.array(
        [widthOffset / 2 * 0.0254, heightOffset * 0.0254, depthOffset * 0.0254]
    ),  # bottom left
]
reefBoxOffsetsRIGHT = [  # in to m
    np.array([-widthOffset / 2 * 0.0254, -heightClearence * 0.0254, 0]),  # top right
    np.array(
        [-widthOffset / 2 * 0.0254, -heightClearence * 0.0254, depthOffset * 0.0254]
    ),  # top left
    np.array(
        [-widthOffset / 2 * 0.0254, heightOffset * 0.0254, depthOffset * 0.0254]
    ),  # bottom left
    np.array([-widthOffset / 2 * 0.0254, heightOffset * 0.0254, 0]),  # bottom right
]
reefBoxOffsetsTOP = [  # in to m
    np.array(
        [widthOffset / 2 * 0.0254, -heightClearence * 0.0254, depthOffset * 0.0254]
    ),
    np.array(
        [-widthOffset / 2 * 0.0254, -heightClearence * 0.0254, depthOffset * 0.0254]
    ),
    np.array([-widthOffset / 2 * 0.0254, -heightClearence * 0.0254, 0]),
    np.array([widthOffset / 2 * 0.0254, -heightClearence * 0.0254, 0]),
]
reefBoxOffsetsBOTTOM = [  # in to m
    np.array([widthOffset / 2 * 0.0254, heightOffset * 0.0254, depthOffset * 0.0254]),
    np.array([-widthOffset / 2 * 0.0254, heightOffset * 0.0254, depthOffset * 0.02540]),
    np.array([-widthOffset / 2 * 0.0254, heightOffset * 0.0254, 0]),
    np.array([widthOffset / 2 * 0.0254, heightOffset * 0.0254, 0]),
]

reefBoxOffsets = [
    reefBoxOffsetsFRONT,
    reefBoxOffsetsLEFT,
    reefBoxOffsetsRIGHT,
    reefBoxOffsetsTOP,
    reefBoxOffsetsBOTTOM,
]


def getClosest3Faces(tag_to_cam_translation, frame):
    pitch, yaw, _ = Calculator.extract_pitch_yaw_roll(
        tag_to_cam_translation, format="XYZ"
    )
    cv2.putText(
        frame, f"h: {yaw:.2f} v: {pitch:.2f}", (0, 40), 0, 1, (255, 255, 255), 1
    )
    horizontal_boxOffset = reefBoxOffsetsLEFT if yaw > 0 else reefBoxOffsetsRIGHT
    vertical_boxOffset = reefBoxOffsetsTOP if pitch < 0 else reefBoxOffsetsBOTTOM
    return [reefBoxOffsetsFRONT, horizontal_boxOffset, vertical_boxOffset]

def transform_basis_from_frc_toimg(T):
    """
    Transforms an affine transformation matrix from a coordinate system where:
    - x is front, y is right, z is up
    to a coordinate system where:
    - z is front, y is down, x is left

    Args:
        T: 4x4 affine transformation matrix

    Returns:
        Transformed 4x4 affine matrix
    """
    # Coordinate transformation rotation matrix (3x3)
    R_P = np.array([[ 0,  -1, 0],
                    [0,  0,  -1],
                    [ 1, 0,  0]])
    

    # Extract rotation and translation from T
    R_T = T[:3, :3]  # Original rotation
    t_T = T[:3, 3]   # Original translation

    # Transform rotation
    R_new = R_P @ R_T @ R_P.T

    # Transform translation
    t_new = R_P @ t_T

    # Construct new affine transformation matrix
    T_new = np.eye(4)
    T_new[:3, :3] = R_new
    T_new[:3, 3] = t_new

    return T_new




# purpleHist = np.load("assets/purpleReefPostHist.npy")
purpleHist = np.load("assets/simulationPurpleReefPost.npy")
purpleThresh = 0.1
fullpurpleThresh = 0.3

Sentinel = getLogger("Reef_Post_Estimator")


class ReefTracker:
    def __init__(
        self,
        cameraIntrinsics: CameraIntrinsics,
        isLocalAT=False,
        cameraExtrinsics: CameraExtrinsics = None,
    ):
        """
        Creates a reef post estimator, that using april tag results will detect coral slots and probabilistically measure if they are occupied\n
        This works by using a color camera along with known extrinsics/intrinsics and known extrinsics for the april tag camera

        Args:
            cameraIntrinsics (`CameraIntrinsics`) : The color camera's intrinsics
            cameraExtrinsics (`CameraExtrinsics`) : The color camera's extrinsics
            atCameraToExtrinsics (`Dict[str,CameraExtrinsics]`) : A mapping of each april tag cameras photonvision name, to the extrinsics of that camera
            photonCommunicator (`PhotonVisionCommunicator`) : An optional field, the class that allows network communication to grab the photonvision april tag results

        """
        self.isLocalAT = isLocalAT
        self.camIntr = cameraIntrinsics
        if not isLocalAT and (
            cameraExtrinsics is None
        ):
            raise Exception(
                "If you are operating in driverStationMode = False, you must provide camera Extrinsics and april tag camera extrinsics!"
            )

        if isLocalAT:
            self.ATPoseGetter = AprilTagLocal(cameraIntrinsics)
        else:
            self.ATPoseGetter = AprilTagSover(camExtr=cameraExtrinsics,camIntr=cameraIntrinsics)

    def __isInFrame(self,u,v):
        return  0 <= u < self.camIntr.getHres() and 0 <= v < self.camIntr.getVres()

    def getAllTracks(self, colorframe, robotPose2dCMRad = None, drawBoxes=True):
        if not self.isLocalAT and robotPose2dCMRad is None:
            raise Exception(
                "If you are operating in driverStationMode = False, you must provide robotPose2dCMRad!"
            )
        
        allTracks = {}
        if self.isLocalAT:
            greyFrame = cv2.cvtColor(colorframe, cv2.COLOR_BGR2GRAY)
            atDetections = self.ATPoseGetter.getDetections(greyFrame)
            atPoses = self.ATPoseGetter.getOrthogonalEstimates(atDetections)
            for detection, pose in zip(atDetections, atPoses):
                coordinates = self.__getTracksForPost(
                    colorframe, pose.pose1.toMatrix(), drawBoxes
                )
                allTracks[detection.getId()] = coordinates

        else:
            ret = self.ATPoseGetter.getNearestAtPose(robotPose2dCMRad)
            print(ret)
            if ret:
                for nearestTagPose, nearestTagId in ret:
                    print(f"{nearestTagId=}")
                    print(f"PRE: {nearestTagPose=}")
                    nearestTagPose = transform_basis_from_frc_toimg(nearestTagPose)
                    print(f"POST: {nearestTagPose=}")
                    nearestTagPose[:3,3] *= 0.01 # cm -> m
                    coordinates = self.__getTracksForPost(
                            colorframe, nearestTagPose, drawBoxes
                        )
                    allTracks[nearestTagId] = coordinates

        return allTracks

    def __getTracksForPost(
        self, colorframe, tagPoseMatrix, drawBoxes
    ):
        if (
            tagPoseMatrix is None
            or np.isclose(tagPoseMatrix[:3, 3], np.zeros(shape=(3))).all()
        ):
            return None

        onScreenBranches = {}
        mask = np.zeros_like(colorframe, dtype=np.uint8)
        frameCopy = colorframe.copy()

        # iterate over each branch of reef
        for offset_idx, offset_3d in cad_to_branch_offset.items():
            # solve camera -> branch via camera -> tag and tag -> branch transformations
            tag_to_reef_homography = np.append(offset_3d, 1.0)  # ensures shape is 4x4
            # if not self.isDriverStation:
            #     tag_to_reef_homography[2] *= -1

            color_camera_to_reef = np.dot(
                tagPoseMatrix,
                tag_to_reef_homography,
            )

            total_color_corners = []
            for reefBoxOffset in getClosest3Faces(tagPoseMatrix, colorframe):
                color_corners = []
                for cornerOffset in reefBoxOffset:
                    box_offset_homogeneous = np.append(cornerOffset, 0)  # Shape: (4,)
                    # if not self.isDriverStation:
                    #     box_offset_homogeneous[2] *= -1

                    tag_to_reef_corner_homography = (
                        tag_to_reef_homography + box_offset_homogeneous
                    )

                    color_camera_to_reef_corner = np.dot(
                        tagPoseMatrix,
                        tag_to_reef_corner_homography,
                    )
                    color_corners.append(color_camera_to_reef_corner)

                total_color_corners.append(color_corners)


            # print(f"{color_camera_to_reef=}")
            # print(f"{tagPoseMatrix=}")

            # project the 3D reef point to 2D image coordinates:
            x_cam, y_cam, z_cam, _ = color_camera_to_reef

            u = (self.camIntr.getFx() * x_cam / z_cam) + self.camIntr.getCx()
            v = (self.camIntr.getFy() * y_cam / z_cam) + self.camIntr.getCy()
            if not self.__isInFrame(u,v):
                continue
            # print(f"{u=} {v=}")

            # project the 3d box corners to 2d image coords
            reef_mask = np.zeros_like(frameCopy)
            total_image_corners = []
            for color_corner in total_color_corners:
                imageCorners = []
                for corner in color_corner:
                    x_cam, y_cam, z_cam, _ = corner
                    uC = (self.camIntr.getFx() * x_cam / z_cam) + self.camIntr.getCx()
                    uV = (self.camIntr.getFy() * y_cam / z_cam) + self.camIntr.getCy()
                    imageCorners.append((int(uC), int(uV)))

                total_image_corners.append(imageCorners)
                # Fill the polygon (the rectangle area) with white (255)
                cv2.fillPoly(mask, [np.int32(imageCorners)], (255, 255, 255))
                cv2.fillPoly(reef_mask, [np.int32(imageCorners)], (255, 255, 255))

            extracted = cv2.bitwise_and(frameCopy, reef_mask)
            lab = cv2.cvtColor(extracted, cv2.COLOR_BGR2LAB)
            backProj = cv2.calcBackProject(
                [lab], [1, 2], purpleHist, [0, 256, 0, 256], 1
            )
            dil = cv2.dilate(backProj, np.ones((2, 2)), iterations=6)
            _, thresh = cv2.threshold(dil, 20, 255, cv2.THRESH_BINARY)
            sum = np.sum(thresh)
            _, baseThresh = cv2.threshold(extracted, 1, 255, cv2.THRESH_BINARY)
            total = np.sum(baseThresh)

            perc = sum / total
            openPercentage = 0
            color = (0, 0, 255)  # red default
            if perc > purpleThresh:
                color = (0, 255, 0)  # green
                openPercentage = perc/fullpurpleThresh

            if drawBoxes:
                cv2.circle(colorframe, (int(u), int(v)), 3, color, 2)
                for imageCorner in total_image_corners:
                    for point1 in imageCorner:
                        for point2 in imageCorner:
                            if point1 != point2:
                                cv2.line(colorframe, point1, point2, color, 1)

                    for imageCorner in imageCorner:
                        uC, uV = imageCorner
                        cv2.circle(colorframe, (int(uC), int(uV)), 1, color, 2)

                cv2.putText(
                    colorframe,
                    f"{offset_idx}",
                    (int(u), int(v) + 30),
                    cv2.FONT_HERSHEY_SIMPLEX,
                    1,
                    color,
                    2,
                )

            onScreenBranches[offset_idx] = (openPercentage)

        # extracted = cv2.bitwise_and(frameCopy, mask)
        # lab = cv2.cvtColor(extracted, cv2.COLOR_BGR2LAB)
        # backProj = cv2.calcBackProject([lab], [1, 2], purpleHist, [0, 256, 0, 256], 1)
        # dil = cv2.dilate(backProj, np.ones((3, 3)), iterations=6)
        # _, thresh = cv2.threshold(dil, 20, 255, cv2.THRESH_BINARY)
        # sum = np.sum(thresh)
        # _, baseThresh = cv2.threshold(extracted, 1, 255, cv2.THRESH_BINARY)
        # total = np.sum(baseThresh)

        # perc = sum / total
        # cv2.putText(extracted, f"P: {perc}", (0, 20), 0, 1, (255, 255, 255), 1)
        # cv2.imshow("extracted", extracted)
        # cv2.imshow("thresh", thresh)

        return onScreenBranches
