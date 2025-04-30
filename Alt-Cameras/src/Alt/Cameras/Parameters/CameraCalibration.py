import os
import json
import codecs
from typing import Optional

import cv2
import numpy as np


class CameraCalibration:
    def __init__(self, cameraMatrix : np.ndarray,  distortionCoeff : np.ndarray, resolutionWH : tuple[int, int]):
        self.cameraMatrix = cameraMatrix
        self.distortionCoeff = distortionCoeff
        self.resolutionWH = resolutionWH
        self.__mapX, self.__mapY = None, None

    def undistortFrame(self, frame : np.ndarray, interpolationMethod = cv2.INTER_LINEAR) -> np.ndarray:
        self.getMapXY() # ensures they exist
        return cv2.remap(frame, self.__mapX, self.__mapY, interpolationMethod)

    def getMapXY(self) -> tuple[np.ndarray]:
        if self.__mapX is None or self.__mapY is None:
            self.__mapX, self.__mapY = self.__getMapXY()

        return self.__mapX, self.__mapY

    def __getMapXY(self) -> tuple[np.ndarray]:
        newCameraMatrix, roi = cv2.getOptimalNewCameraMatrix(
            self.cameraMatrix, self.distortionCoeff, self.resolutionWH, 1, self.resolutionWH
        )

        # Generate undistortion and rectification maps
        mapx, mapy = cv2.initUndistortRectifyMap(
            self.cameraMatrix, self.distortionCoeff, None, newCameraMatrix, self.resolutionWH, cv2.CV_32FC1
        )

        return mapx, mapy

    def fromJsonPath(path : str) -> Optional["CameraCalibration"]:
        try:
            with open(path) as calibration:
                data = json.load(calibration)

                resolution = data["resolution"]

                cameraMatrix = np.array(data["CameraMatrix"])
                distCoeffs = np.array(data["DistortionCoeff"])
                # print(cameraMatrix)
                # Compute the optimal new camera matrix
                w = int(resolution["width"])
                h = int(resolution["height"])

                return CameraCalibration(cameraMatrix, distCoeffs, (w, h))

        except Exception as e:
            print(f"Failed to open config! {e}")
            return None
    
    @staticmethod
    def saveJson(cameraCalibration : "CameraCalibration", path : str):
        if not path.endswith(".json"):
            path = f"{path}.json"
        os.makedirs(path, exist_ok=True)

        calibrationJSON = {
            "CameraMatrix": cameraCalibration.cameraMatrix.tolist(),
            "DistortionCoeff": cameraCalibration.distortionCoeff.tolist(),
            "resolution": {"width": cameraCalibration.resolutionWH[0], "height": cameraCalibration.resolutionWH[1]},
        }

        json.dump(
            calibrationJSON,
            codecs.open(path, "w", encoding="utf-8"),
            separators=(",", ":"),
            sort_keys=True,
            indent=4,
        )