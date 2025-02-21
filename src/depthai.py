# from tools import calibration
# calibration.takeCalibrationPhotos(1,"assets/TMPImages",5,(1280,960))

# import depthai as dai

# import numpy as np

# Create a DepthAI device and get calibration data
# with dai.Device() as device:
#     calib_data = device.readCalibration()

#     # Get intrinsics for the RGB camera at 1920x1080 resolution
#     intrinsics = calib_data.getCameraIntrinsics(dai.CameraBoardSocket.RGB, 1920, 1080)

#     # Convert to NumPy array for easy handling
#     K = np.array(intrinsics).reshape(3,3)

#     print("Camera Intrinsics Matrix (K):")
#     print(K)
# exit()

import depthai as dai

import numpy as np
import sys
from pathlib import Path
import math
import cv2

np.set_printoptions(suppress=True)

# resize intrinsics on host doesn't seem to work well for RGB 12MP
def resizeIntrinsicsFW(
    intrinsics, width, height, destWidth, destHeight, keepAspect=True
):
    scaleH = destHeight / height
    scaleW = destWidth / width
    if keepAspect:
        scaleW = max(scaleW, scaleH)
        scaleH = scaleW

    scaleMat = np.array([[scaleW, 0, 0], [0, scaleH, 0], [0, 0, 1]])
    scaledIntrinscs = scaleMat @ intrinsics

    if keepAspect:
        if scaleW * height > destHeight:
            scaledIntrinscs[1][2] -= (height * scaleW - destHeight) / 2.0
        elif scaleW * width > destWidth:
            scaledIntrinscs[0][2] -= (width * scaleW - destWidth) / 2.0

    return scaledIntrinscs


def getHFov(intrinsics, width):
    fx = intrinsics[0][0]
    fov = 2 * 180 / (math.pi) * math.atan(width * 0.5 / fx)
    return fov


def getVFov(intrinsics, height):
    fy = intrinsics[1][1]
    fov = 2 * 180 / (math.pi) * math.atan(height * 0.5 / fy)
    return fov


def getDFov(intrinsics, w, h):
    fx = intrinsics[0][0]
    fy = intrinsics[1][1]
    return np.degrees(2 * np.arctan(np.sqrt(w * w + h * h) / (((fx + fy)))))


# Connect Device
with dai.Device() as device:

    calibData = device.readCalibration()

    cameras = device.getConnectedCameras()

    alpha = 1

    for cam in cameras:
        M, width, height = calibData.getDefaultIntrinsics(cam)
        M = np.array(M)
        print(f"Camera Name: {cam}")
        print(f"M: {M} {width=} {height=}")
        d = np.array(calibData.getDistortionCoefficients(cam))

        hFov = getHFov(M, width)
        vFov = getVFov(M, height)
        dFov = getDFov(M, width, height)

        print("FOV measurement from calib (e.g. after undistortion):")
        print(f"{cam}")
        print(f"Horizontal FOV: {hFov}")
        print(f"Vertical FOV: {vFov}")
        print(f"Diagonal FOV: {dFov}")

        M, _ = cv2.getOptimalNewCameraMatrix(M, d, (width, height), alpha)
        hFov = getHFov(M, width)
        vFov = getHFov(M, height)
        dFov = getDFov(M, width, height)

        print()
        print(
            f"FOV measurement with optimal camera matrix and alpha={alpha} (e.g. full sensor FOV, without undistortion):"
        )
        print(f"{cam}")
        print(f"Horizontal FOV: {hFov}")
        print(f"Vertical FOV: {vFov}")
        print(f"Diagonal FOV: {dFov}")

        print()
        print("=============")
        print()
