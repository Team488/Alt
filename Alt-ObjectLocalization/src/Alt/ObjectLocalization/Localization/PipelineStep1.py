import time
import random

import cv2
import numpy as np
from Alt.Core import getChildLogger
from Alt.Core.Units.Poses import Pose2d, Transform3d
from Alt.Cameras.Parameters.CameraIntrinsics import CameraIntrinsics
from Alt.Cameras.Parameters.CameraExtrinsics import CameraExtrinsics

from ..Constants.Inference import DefaultConfigConstants
from ..inference.ModelConfig import ModelConfig
from ..inference.MultiInferencer import MultiInferencer
from ..inference.utils import drawBox
from ..Tracking.deepSortBaseLabler import DeepSortBaseLabler
from .positionTranslations import CameraToRobotTranslator, transformWithYaw, transformWithOffset
from .positionEstimator import RelativePositionEstimator
from .LocalizationResult import LocalizationResult

Sentinel = getChildLogger("Localization_Pipeline_Step1")

class PipelineStep1:
    def __init__(self,
        modelConfig : ModelConfig,
        cameraIntrinsics: CameraIntrinsics,
        cameraExtrinsics: CameraExtrinsics,
    ) -> None:
        self.modelConfig = modelConfig
        self.labelNames = [label.name for label in self.modelConfig.getObjects()]
        self.cameraIntrinsics = cameraIntrinsics
        self.cameraExtrinsics = cameraExtrinsics
        self.inferencer = None

    def initialize(self):
        self.inferencer = MultiInferencer(self.modelConfig)
        self.baseLabler = DeepSortBaseLabler(len(self.modelConfig.getObjects()))
        self.relativeEstimator = RelativePositionEstimator(self.cameraIntrinsics, self.modelConfig.getObjects())
        self.translator = CameraToRobotTranslator()
        # for drawing tracked detections
        self.colors = [
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for _ in range(15)
        ]


    def runStep1(
        self,
        robotPose : Pose2d ,
        colorFrame : np.ndarray,
        depthFrameMM : np.ndarray=None,
        minConf : float = DefaultConfigConstants.confThreshold,
        drawBoxes : bool = DefaultConfigConstants.drawBoxes,
        maxDetections : int = DefaultConfigConstants.maxDetection,
    ) -> list[LocalizationResult]:
        startTime = time.time()

        # yolo inference
        yoloResults = self.inferencer.run(
            colorFrame, minConf=minConf, drawBoxes=False
        ) 

        # output ordering should already be sorted in descending order
        # so we can just splice from the start
        if maxDetections != None:
            yoloResults = yoloResults[:maxDetections]

        # no results
        if len(yoloResults) == 0:
            if drawBoxes:
                endTime = time.time()
                fps = 1 / (endTime - startTime)
                cv2.putText(colorFrame, f"FPS:{fps}", (10, 20), 0, 1, (0, 255, 0), 2)
            return []

        # id(unique),bbox,conf,isrobot,features,
        labledResults = self.baseLabler.labelResults(colorFrame, yoloResults)

        # draw the tracked deepsort results
        if drawBoxes:
            # draw a box with id,conf and relative estimate
            for labledResult in labledResults:
                label = "INVALID"  # technically redundant, as the deepsort step filters out any invalid class_idxs
                if 0 <= labledResult.class_idx < len(self.labelNames):
                    label = f"{self.labelNames[labledResult.class_idx]} Id:{labledResult.deepsort_id}"

                color = self.colors[labledResult.deepsort_id % len(self.colors)]
                drawBox(colorFrame, labledResult.bbox, label, labledResult.conf, color)

        finalResults = []
        for labledResult in labledResults:
            relativeTransform = self.relativeEstimator.getRelativePositionEstimate(labledResult, colorFrame, depthFrameMM)
            relToRobot = self.translator.turnCameraCoordinatesIntoRobotCoordinates(relativeTransform, self.cameraExtrinsics)
            rotated = transformWithYaw(relToRobot, robotPose.yaw)
            absolute = rotated.add(Transform3d(robotPose.x, robotPose.y, 0))
            finalResults.append(LocalizationResult(absolute, labledResult.class_idx, labledResult.conf, labledResult.deepsort_id, labledResult.features))

        endTime = time.time()

        fps = 1 / (endTime - startTime)

        if drawBoxes:
            # add final fps
            cv2.putText(colorFrame, f"FPS:{fps}", (10, 20), 0, 1, (0, 255, 0), 2)

        return finalResults

