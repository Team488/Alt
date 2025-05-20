import math
import json
from typing import Optional, Union

import numpy as np

from ..Parameters.CameraCalibration import CameraCalibration


class CameraIntrinsics:
    def __init__(
        self,
        width_pix: int = -1,
        height_pix: int = -1,
        hfov_rad: float = -1,
        vfov_rad: Union[float, int] = -1,
        focal_length_mm: float = -1,
        pixel_size_mm: float = -1,
        sensor_size_mm: float = -1,
        fx_pix: float = -1,
        fy_pix: Union[int, float] = -1,
        cx_pix: Union[int, float] = -1,
        cy_pix: Union[int, float] = -1,
    ) -> None:
        self.value = (
            (width_pix, height_pix),  # Resolution
            (hfov_rad, vfov_rad),  # FOV
            (focal_length_mm, pixel_size_mm, sensor_size_mm),  # Physical Constants
            (fx_pix, fy_pix),  # Calibrated Fx, Fy
            (cx_pix, cy_pix),  # Calibrated Cx, Cy
        )

    """
    Create camera intrinsics at runtime.\n
    WARNING, any unfilled values may cause errors down the line. Please override default values you know you need
    """

    def getHres(self) -> float:
        return self.value[0][0]

    def getVres(self) -> float:
        return self.value[0][1]

    def getHFovRad(self) -> float:
        return self.value[1][0]

    def getVFovRad(self) -> float:
        return self.value[1][1]

    def getFocalLengthMM(self) -> float:
        return self.value[2][0]

    def getPixelSizeMM(self) -> float:
        return self.value[2][1]

    def getSensorSizeMM(self) -> float:
        return self.value[2][2]

    def getFx(self) -> float:
        assert len(self.value) > 3
        return self.value[3][0]

    def getFy(self) -> float:
        assert len(self.value) > 3
        return self.value[3][1]

    def getCx(self) -> float:
        assert len(self.value) > 4
        return self.value[4][0]

    def getCy(self) -> float:
        assert len(self.value) > 4
        return self.value[4][1]

    def __str__(self):
        return f"({self.getHres()}x{self.getVres()})-(fx:{self.getFx()}|fy:{self.getFy()}|cx:{self.getCx()}|cy:{self.getCy()})"
    
    def getCameraMatrix(self) -> np.ndarray:
        return np.array([[self.getFx(), 0, self.getCx()],[0, self.getFy(), self.getCy()],[0, 0, 1]])


    @staticmethod
    def getHfov(cameraIntr: "CameraIntrinsics", radians: bool = True):
        hres = cameraIntr.getHres()
        fx = cameraIntr.getFx()

        rad = 2 * math.atan(hres / (2 * fx))
        if radians:
            return rad
        return math.degrees(rad)

    @staticmethod
    def getVfov(cameraIntr: "CameraIntrinsics", radians: bool = True):
        vres = cameraIntr.getVres()
        fy = cameraIntr.getFx()

        rad = 2 * math.atan(vres / (2 * fy))
        if radians:
            return rad
        return math.degrees(rad)

    @staticmethod
    def fromPhotonConfig(photonConfigPath) -> Optional["CameraIntrinsics"]:
        try:
            with open(photonConfigPath) as PV_config:
                data = json.load(PV_config)

                cameraIntrinsics = data["cameraIntrinsics"]["data"]
                fx = cameraIntrinsics[0]
                fy = cameraIntrinsics[4]
                cx = cameraIntrinsics[2]
                cy = cameraIntrinsics[5]

                width = int(data["resolution"]["width"])
                height = int(data["resolution"]["height"])

                return CameraIntrinsics(
                    width_pix=width,
                    height_pix=height,
                    fx_pix=fx,
                    fy_pix=fy,
                    cx_pix=cx,
                    cy_pix=cy,
                )

        except Exception as e:
            print(f"Failed to open config! {e}")
            return None

    @staticmethod
    def fromCustomConfig(customConfigPath : str) -> Optional["CameraIntrinsics"]:
        try:
            with open(customConfigPath) as custom_config:
                data = json.load(custom_config)

                cameraIntrinsics = data["CameraMatrix"]
                fx = cameraIntrinsics[0][0]
                fy = cameraIntrinsics[1][1]
                cx = cameraIntrinsics[0][2]
                cy = cameraIntrinsics[1][2]

                width = int(data["resolution"]["width"])
                height = int(data["resolution"]["height"])

                return CameraIntrinsics(
                    width_pix=width,
                    height_pix=height,
                    fx_pix=fx,
                    fy_pix=fy,
                    cx_pix=cx,
                    cy_pix=cy,
                )

        except Exception as e:
            print(f"Failed to open config! {e}")
            return None

    @staticmethod
    def fromCustomConfigLoaded(loadedConfig : dict):
        data = loadedConfig

        cameraIntrinsics = data["CameraMatrix"]
        fx = cameraIntrinsics[0][0]
        fy = cameraIntrinsics[1][1]
        cx = cameraIntrinsics[0][2]
        cy = cameraIntrinsics[1][2]

        width = int(data["resolution"]["width"])
        height = int(data["resolution"]["height"])

        return CameraIntrinsics(
            width_pix=width,
            height_pix=height,
            fx_pix=fx,
            fy_pix=fy,
            cx_pix=cx,
            cy_pix=cy,
        )
        
    @staticmethod
    def fromCameraCalibration(calibration : CameraCalibration):

        fx = calibration.cameraMatrix[0][0]
        fy = calibration.cameraMatrix[1][1]
        cx = calibration.cameraMatrix[0][2]
        cy = calibration.cameraMatrix[1][2]


        return CameraIntrinsics(
            width_pix=calibration.resolutionWH[0],
            height_pix=calibration.resolutionWH[1],
            fx_pix=fx,
            fy_pix=fy,
            cx_pix=cx,
            cy_pix=cy,
        )



