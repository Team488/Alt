import os
from typing import Optional

from Alt.Core.Utils.files import user_data_dir
from ..Parameters.CameraIntrinsics import CameraIntrinsics
from ..Parameters.CameraCalibration import CameraCalibration


class CalibrationUtil:
    CALIBPREFIX = "Calibrations"
    def __init__(self, cameraName : str):
        self.cameraName = cameraName
        self.__savePath = os.path.join(str(user_data_dir), self.CALIBPREFIX, self.cameraName + ".json")
        self.__calibration = self.getCalibration()

    def getCalibration(self) -> Optional[CameraCalibration]:
        if not hasattr(self, '__calibration') or self.__calibration is None:
            self.__calibration = CameraCalibration.fromJsonPath(self.__savePath)
        
        return self.__calibration
    
    def getIntrinsics(self) -> Optional[CameraIntrinsics]:
        calib = self.getCalibration()
        if calib is None:
            return None
        
        return CameraIntrinsics.fromCameraCalibration(calib)
    
    def setNewCalibration(self, calibration : "CameraCalibration"):
        self.__calibration = calibration
        self.__saveCalibration()
    
    def __saveCalibration(self):
        if self.__calibration is None:
            raise RuntimeError("Cannot save calibration as it is None!")
        
        CameraCalibration.saveJson(self.__calibration, self.__savePath)

