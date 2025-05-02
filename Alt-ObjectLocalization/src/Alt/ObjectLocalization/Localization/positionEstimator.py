import math

import numpy as np
from Alt.Core import getChildLogger
from Alt.Core.Units import Conversions
from Alt.Core.Units.Poses import Transform3d
from Alt.Cameras.Parameters.CameraIntrinsics import CameraIntrinsics

from ..Constants.Inference import Object
from .DepthEstimationMethod import DepthEstimationMethod
from ..Detections.DetectionResult import DetectionResult

Sentinel = getChildLogger("Position_Estimator")

class RelativePositionEstimator:
    def __init__(self, cameraIntrinsics : CameraIntrinsics, objects : list[Object],):
        self.cameraIntrinsics = cameraIntrinsics
        self.objects = objects
        self.nClasses = len(self.objects)

    def getRelativePositionEstimate(
        self,
        result : DetectionResult,
        colorFrame : np.ndarray,
        depthFrameMM : np.ndarray = None
    ) -> Transform3d:
        if result.class_idx < 0 or result.class_idx >= len(self.objects):
            Sentinel.warning("Out of bounds class_idx!")
            return None

        object_ = self.objects[result.class_idx]
        
        if object_.depthMethod is None:
            Sentinel.debug(f"{object_.name} has no depthMethod.")
            return None

        if object_.depthMethod.usesDepth():
            # cannot satisfy depth requirement
            if depthFrameMM is None:
                Sentinel.debug(f"No depth frame for {object_.name}'s depthmethod.")
                return None
            
            # depth
            return self.__estimateRelativePosition(depthFrameMM, result.bbox, self.cameraIntrinsics, object_)
        
        # color
        return self.__estimateRelativePosition(colorFrame, result.bbox, self.cameraIntrinsics, object_)

    def __calcBearing(self, fov, res, pixelDiff):
        fovperPixel = fov / res
        return pixelDiff * fovperPixel
            
    def __estimateRelativePosition(
        self, frame : np.ndarray, boundingBox : tuple, cameraIntrinsics: CameraIntrinsics, depthMethod : DepthEstimationMethod
    ) -> Transform3d:
        x1, y1, x2, y2 = Conversions.toint(boundingBox)
        centerX = (x1 + x2) / 2
        centerY = (y1 + y2) / 2

        croppedImg = self.__crop_image(frame, (x1, y1), (x2, y2), safety_margin=0.07)
        
        depth = depthMethod.getDepthEstimateCM(croppedImg, cameraIntrinsics)
        if not depth:
            return None
        
        bearingH = self.__calcBearing(
            cameraIntrinsics.getHFovRad(),
            cameraIntrinsics.getHres(),
            int(centerX - cameraIntrinsics.getCx()),
        )
        # positive when centerX > cX. 
        # However in frc coordinate system, y (horizontal) is flipped
        # so negate it
        bearingH *= -1

        bearingV = self.__calcBearing(
            cameraIntrinsics.getVFovRad(),
            cameraIntrinsics.getVres(),
            int(centerY - cameraIntrinsics.getCy()),
        )
        
        Sentinel.debug(f"{depth=} {bearingH=} {bearingV=}")

        x,y,z = self.__componentizeHDistAndBearingHV(depth, bearingH, bearingV)
        return Transform3d(x, y, z)
    
    """ This follows the idea that the distance we calculate is independent to bearing. This means that the distance value we get is the X dist. Thus y will be calculated using bearing
        Takes hDist, bearing H/V (radians) and returns x,y,z
    """

    #TODO Cheeck this

    def __componentizeHDistAndBearingHV(self, hDist : float, bearingH : float, bearingV : float):
        x = hDist
        y = math.tan(bearingH) * hDist
        z = math.tan(bearingV) * hDist
        return x, y, z



