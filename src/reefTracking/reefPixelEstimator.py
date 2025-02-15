"""
https://robotpy.readthedocs.io/projects/apriltag/en/latest/robotpy_apriltag.html
https://pypi.org/project/photonlibpy/
PORT TO PHOTONVISION LATER: https://docs.photonvision.org/en/latest/docs/programming/photonlib/index.html

Steps:
1. Get the pose of AT
2. Find the 3D offsets of the AT -> reef branches (have a cad model for that)
3. Transform locations of reef branches via depth data -> camera frame
4. Detect if objects are "fixed" onto those branches

Measurement in inches
"""
import cv2
import numpy as np
from robotpy_apriltag import (
    AprilTagField,
    AprilTagFieldLayout,
    AprilTagDetector,
    AprilTagPoseEstimator,
)

from wpimath.geometry import Transform3d
import json

from reefTracking.aprilTagHelper import AprilTagHelper


### CAD Offset:
### X = Downwards -> Right
### Y = Upwards -> Right
### Z = Upwards

# Measurement is in Inches

# CAD to tip of the rod. (MAX Distance)
cad_to_branch_offset = {
    "L2-L": np.array([-6.756, -19.707, 2.608]),
    "L2-R": np.array([6.754, -19.707, 2.563]),
    "L3-L": np.array([-6.639, -35.606, 2.628]),
    "L3-R": np.array([6.637, -35.606, 2.583]),
    "L4-L": np.array([-6.470, -58.4175, 0.921]),  # NOT MODIFIED
    "L4-R": np.array([6.468, -58.4175, 0.876]),  # NOT MODIFIED
}


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


# Convert to meters:
for branch, offset in cad_to_branch_offset.items():
    for i in range(len(offset)):
        offset[i] *= 0.0254


class ReefPixelEstimator:
    def __init__(self, config_file="assets/config/1280x800v1.json"):
        self.helper = AprilTagHelper(config_file)
        self.loadConfig(config_file)

    def loadConfig(self, config_file):
        try:
            with open(config_file) as PV_config:
                data = json.load(PV_config)

                self.cameraIntrinsics = data["cameraIntrinsics"]["data"]
                self.fx = self.cameraIntrinsics[0]
                self.fy = self.cameraIntrinsics[4]
                self.cx = self.cameraIntrinsics[2]
                self.cy = self.cameraIntrinsics[5]

                self.K = np.array(
                    [[self.fx, 0, self.cx], [0, self.fy, self.cy], [0, 0, 1]],
                    dtype=np.float32,
                )

                self.width = int(data["resolution"]["width"])
                self.height = int(data["resolution"]["height"])

                distCoeffsSize = int(data["distCoeffs"]["cols"])
                self.distCoeffs = np.array(
                    data["distCoeffs"]["data"][0:distCoeffsSize], dtype=np.float32
                )
        except Exception as e:
            print(f"Failed to open config! {e}")

    def getReefCoordinates(self, image, drawCoordinates=True):
        grayscale_image = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        outputs = self.helper.getDetections(grayscale_image)
        orthogonalEsts = self.helper.getOrthogonalEstimates(outputs)
        coordinates = {}
        for tag_pose_estimation_orthogonal, output in zip(orthogonalEsts, outputs):
            print("ID", output.getId())

            if drawCoordinates:
                # Retrieve the corners of the AT detection
                points = []
                for corner in range(0, 4):
                    x = output.getCorner(corner).x
                    y = output.getCorner(corner).y
                    points.append([x, y])
                points = np.array(points, dtype=np.int32)
                points = points.reshape((-1, 1, 2))
                cv2.polylines(
                    frame, [points], isClosed=True, color=(0, 255, 255), thickness=3
                )

                # Retrieve the center of the AT detection
                centerX = output.getCenter().x
                centerY = output.getCenter().y
                cv2.circle(
                    frame,
                    (int(centerX), int(centerY)),
                    2,
                    color=(0, 255, 255),
                    thickness=3,
                )

            tag_pose_estimation_orthogonal_pose1_matrix = (
                tag_pose_estimation_orthogonal.pose1
            )
            tag_pose_estimation_orthogonal_pose2_matrix = (
                tag_pose_estimation_orthogonal.pose2
            )
            # print(f"regular: x: {tag_pose_estimation.x}, y: {tag_pose_estimation.y}, z: {tag_pose_estimation.z}")
            print(
                f"orthogonal pose 1: x: {tag_pose_estimation_orthogonal_pose1_matrix.x}, y: {tag_pose_estimation_orthogonal_pose1_matrix.y}, z: {tag_pose_estimation_orthogonal_pose1_matrix.z}"
            )
            # print(f"orthogonal pose 2: x: {tag_pose_estimation_orthogonal_pose2_matrix.x}, y: {tag_pose_estimation_orthogonal_pose2_matrix.y}, z: {tag_pose_estimation_orthogonal_pose2_matrix.z}")
            # print("===============")

            onScreenBranches = {}
            for offset_idx, offset_3d in cad_to_branch_offset.items():
                # solve camera -> branch via camera -> tag and tag -> branch transformations
                tag_to_reef_homography = np.append(
                    offset_3d, 1.0
                )  # ensures shape is 4x4
                # camera_to_reef = np.dot(tag_pose_estimation_matrix, tag_to_reef_homography)
                camera_to_reef = np.dot(
                    tag_pose_estimation_orthogonal_pose1_matrix.toMatrix(),
                    tag_to_reef_homography,
                )

                x_cam, y_cam, z_cam, _ = camera_to_reef

                # project the 3D point to 2D image coordinates:
                u = (self.fx * x_cam / z_cam) + self.cx
                v = (self.fy * y_cam / z_cam) + self.cy

                if drawCoordinates:
                    cv2.circle(frame, (int(u), int(v)), 5, (0, 255, 255), 2)
                    cv2.putText(
                        frame,
                        f"{offset_idx}",
                        (int(u), int(v) + 30),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        1,
                        (255, 255, 255),
                        2,
                    )

                onScreenBranches[offset_idx] = (u, v)

            coordinates[output.getId()] = onScreenBranches

        return coordinates
