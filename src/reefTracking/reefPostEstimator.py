import time
import cv2
import json
import numpy as np
from typing import Dict
from wpimath.geometry import Transform3d
from reefTracking.photonvisionComminicator import PhotonVisionCommunicator
from tools.Constants import CameraIntrinsics, CameraExtrinsics, ATCameraExtrinsics
from tools import Calculator
from Core import getLogger

### CAD Offset:
### X = Downwards -> Right
### Y = Upwards -> Right
### Z = Upwards

# Measurement is in Inches

# CAD to tip of the rod. (MAX Distance)
cad_to_branch_offset = {
    "L2-L": np.array([-6.756, 19.707, 2.608]),
    "L2-R": np.array([6.754, 19.707, 2.563]),
    "L3-L": np.array([-6.639, 35.606, 2.628]),
    "L3-R": np.array([6.637, 35.606, 2.583]),
    "L4-L": np.array([-6.470, 58.4175, 0.921]),  # NOT MODIFIED
    "L4-R": np.array([6.468, 58.4175, 0.876]),  # NOT MODIFIED
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



zoffset = 3 # in
widthOffset = 6  # in                                                                   #               ↖  (z)
heightOffset = 12  # in                                                                 #                (3)
heightClearence = 1                                                                     #                  \
reefBoxOffsets = [      # in to m                                                       #                   \
    np.array([widthOffset / 2 * 0.0254, heightClearence * 0.0254, 0]),                 # (1)  (x) <(1)------o
    np.array([-widthOffset / 2 * 0.0254, -heightOffset * 0.0254, 0]),                    # (2)                | 
    np.array([-widthOffset / 2 * 0.0254, heightClearence * 0.0254, zoffset* 0.0254]),  # (3)               (2)
]                                                                                       #                    ↓ (y)
                                                                                        #                       
                                                                                        # all corners of a imaginary box around a point on the reef


Sentinel = getLogger("Reef_Post_Estimator")
class ReefPostEstimator:
    def __init__(self, cameraIntrinsics : CameraIntrinsics, cameraExtrinsics : CameraExtrinsics, atCameraToExtrinsics : list[ATCameraExtrinsics],
                 photonCommunicator : PhotonVisionCommunicator = PhotonVisionCommunicator(useNetworkTables=True)):
        """
        Creates a reef post estimator, that using april tag results will detect coral slots and probabilistically measure if they are occupied\n
        This works by using a color camera along with known extrinsics/intrinsics and known extrinsics for the april tag camera

        Args:
            cameraIntrinsics (`CameraIntrinsics`) : The color camera's intrinsics
            cameraExtrinsics (`CameraExtrinsics`) : The color camera's extrinsics
            atCameraToExtrinsics (`Dict[str,CameraExtrinsics]`) : A mapping of each april tag cameras photonvision name, to the extrinsics of that camera
            photonCommunicator (`PhotonVisionCommunicator`) : An optional field, the class that allows network communication to grab the photonvision april tag results

        """
        self.camIntr = cameraIntrinsics
        self.camExtr = cameraExtrinsics
        self.camTransform = self.camExtr.get4x4AffineMatrixMeters()
        # get at cam transforms using T(r -> bw)^-1 @ T(r -> c) = T(bw -> c) 
        self.atTransforms =  {atIntrinsic.getPhotonCameraName(): Calculator.inverse4x4Affline(atIntrinsic.get4x4AffineMatrixMeters())@self.camTransform for atIntrinsic in atCameraToExtrinsics}
        self.photonCommunicator = photonCommunicator

    def estimatePosts(self, colorframe, drawBoxes = True):
        coordinates = {}
        for key, bw_to_color_transform in self.atTransforms.items():
            tagPoseMatrix = self.photonCommunicator.getTagPoseAsMatrix(key)
            if tagPoseMatrix is None or np.isclose(tagPoseMatrix[:3,3], np.zeros(shape=(3))).all():
                Sentinel.warning(f"Not able to access april tag results for: {key=}")
                continue


            onScreenBranches = {}
            # iterate over each branch of reef
            for offset_idx, offset_3d in cad_to_branch_offset.items():
                # solve camera -> branch via camera -> tag and tag -> branch transformations
                tag_to_reef_homography = np.append(
                    offset_3d, 1.0
                )  # ensures shape is 4x4

                bw_camera_to_reef = np.dot(
                    tagPoseMatrix,
                    tag_to_reef_homography,
                )


                bw_corners = []
                for boxOffset in reefBoxOffsets:
                    box_offset_homogeneous = np.append(boxOffset, 0)  # Shape: (4,)
                    tag_to_reef_corner_homography = (
                        tag_to_reef_homography + box_offset_homogeneous
                    )

                    bw_camera_to_reef_corner = np.dot(
                        tagPoseMatrix,
                        tag_to_reef_corner_homography,
                    )
                    bw_corners.append(bw_camera_to_reef_corner)

                color_camera_to_reef = bw_camera_to_reef @ bw_to_color_transform

                print(f"{bw_camera_to_reef=}")
                print(f"{color_camera_to_reef=}")
                print(f"{tagPoseMatrix=}")

                color_corners = [corner @ bw_to_color_transform for corner in bw_corners]

                x_cam, y_cam, z_cam, _ = color_camera_to_reef


                # project the 3D point to 2D image coordinates:
                u = (self.camIntr.getFx() * x_cam / z_cam) + self.camIntr.getCx()
                v = (self.camIntr.getFy() * y_cam / z_cam) + self.camIntr.getCy()

                print(f"{u=} {v=}")

                # project the 3d box corners to 2d image coords
                imageCorners = []
                for corner in color_corners:
                    x_cam, y_cam, z_cam, _ = corner
                    print(f"{corner=}")
                    uC = (self.camIntr.getFx() * x_cam / z_cam) + self.camIntr.getCx()
                    uV = (self.camIntr.getFy() * y_cam / z_cam) + self.camIntr.getCy()
                    imageCorners.append((uC, uV))

                if drawBoxes:
                    cv2.circle(colorframe, (int(u), int(v)), 5, (0, 255, 255), 2)
                    min_x, min_y = np.min(imageCorners, axis=0)
                    max_x, max_y = np.max(imageCorners, axis=0)
                    cv2.rectangle(
                        colorframe,
                        (int(min_x), int(min_y)),
                        (int(max_x), int(max_y)),
                        (255, 255, 255),
                        2,
                    )

                    for imageCorner in imageCorners:
                        uC, uV = imageCorner
                        cv2.circle(colorframe, (int(uC), int(uV)), 3, (255, 255, 255), 2)

                    cv2.putText(
                        colorframe,
                        f"{offset_idx}",
                        (int(u), int(v) + 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (255, 255, 255),
                        2,
                    )

                onScreenBranches[offset_idx] = (u, v)

            coordinates[key] = onScreenBranches

        return coordinates





            
