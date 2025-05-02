from abc import abstractmethod, ABC

import numpy as np
from Alt.Cameras.Parameters.CameraIntrinsics import CameraIntrinsics

class DepthEstimationMethod(ABC):
    @abstractmethod
    def getDepthEstimateCM(self, croppedBBox : np.ndarray, cameraIntrinsics : CameraIntrinsics) -> float:
        """ Base cropped frame depth estimate method"""
        pass
    
    @abstractmethod
    def usesDepth(self) -> bool:
        pass

class KnownSizeMethod(DepthEstimationMethod):
    def getDepthEstimateCM(self, croppedColorBBoxFrame : np.ndarray, cameraIntrinsics : CameraIntrinsics) -> float:
        """ Given a cropped color frame of the objects bounding box, return a depth estimate"""
        if self.isHorizontalSize():
            focalLength = cameraIntrinsics.getFx()
        else:
            focalLength = cameraIntrinsics.getFy()

        return self.__calculateDistance(self.getObjectSizeCM(), self.getObjectSizePixels(croppedColorBBoxFrame), focalLength)

    def usesDepth(self) -> bool:
        return False

    def __calculateDistance(self, knownSize, currentSizePixels, focalLengthPixels) -> float:
        # using similar triangles derived camera equation
        return (knownSize * focalLengthPixels) / (currentSizePixels)

    @abstractmethod
    def getObjectSizePixels(self, croppedColorBBoxFrame : np.ndarray):
        pass

    @abstractmethod
    def getObjectSizeCM(self):
        pass
    
    @abstractmethod
    def isHorizontalSize(self) -> bool:
        """ Is the object normally roughly horizontally spanning the screen, or vertically"""
        pass
    

class DepthCameraMethod(DepthEstimationMethod):
    def getDepthEstimateCM(self, croppedDepthBBoxFrameMM : np.ndarray, cameraIntrinsics : CameraIntrinsics) -> float:
        """ Given a cropped depth frame of the objects bounding box, return a depth estimate"""
        return self.getDepthValueCM(croppedDepthBBoxFrameMM / 10) # mm -> cm

    def usesDepth(self) -> bool:
        return True

    @abstractmethod
    def getDepthValueCM(self, croppedDepthBBoxFrameCM : np.ndarray) -> float:
        """ Probe depth frame and return the depth value expected given its centered on the bounding box of the detected object"""
        pass


class CentralProbingDepthMethod(DepthCameraMethod):
    def getDepthValueCM(self, croppedDepthBBoxFrameCM : np.ndarray):
        # get center of the frame
        centerPoint = croppedDepthBBoxFrameCM.shape[:2] // 2
        x, y = map(int, centerPoint)
        
        # batch size is how big of a probing of the center to take
        batch = self.getBatchSize()
        
        # bounds clipping
        mx = max(0, x - batch)
        my = max(0, y - batch)
        lx = min(croppedDepthBBoxFrameCM.shape[1], x + batch)
        ly = min(croppedDepthBBoxFrameCM.shape[0], y + batch)

        # return average of all in batch
        return np.mean(croppedDepthBBoxFrameCM[my:ly][mx:lx]) / 10
    
    def getBatchSize(self) -> int:
        return 5