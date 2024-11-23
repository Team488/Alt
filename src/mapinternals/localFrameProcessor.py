import random
import time
from mapinternals.deepSortBaseLabler import DeepSortBaseLabler
from tools.Constants import CameraIntrinsics, CameraExtrinsics, MapConstants
from tools.positionEstimator import PositionEstimator
from tools.positionTranslations import CameraToRobotTranslator
import numpy as np
import cv2

""" This handles the full pipline from a frame to detections with deepsort id's. You can think of it as the local part of the detection pipeline
    After this detections are centralized over the network to an orin and thats where the Ukf and etc will reside
"""


class LocalFrameProcessor:
    def __init__(
        self,
        cameraIntrinsics: CameraIntrinsics,
        cameraExtrinsics: CameraExtrinsics,
        useRknn = False
    ) -> None:
        if useRknn:
            from inference.rknnInferencer import rknnInferencer
            self.inf = rknnInferencer()
        else:
            from inference.onnxInferencer import onnxInferencer
            self.inf = onnxInferencer()
        self.baseLabler: DeepSortBaseLabler = DeepSortBaseLabler()
        self.cameraIntrinsics: CameraIntrinsics = cameraIntrinsics
        self.cameraExtrinsics: CameraExtrinsics = cameraExtrinsics
        self.estimator = PositionEstimator()
        self.translator = CameraToRobotTranslator()
        self.colors = [
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for j in range(15)
        ]

    def processFrame(
        self, frame, robotPosX=0, robotPosY=0, robotPosZ=0, drawBoxes=True
    ) -> list[list[int, tuple[int, int, int], float, bool, np.ndarray]]:
        startTime = time.time()
        rknnResults = self.inf.inferenceFrame(frame)
        
        if not rknnResults:
            endTime = time.time()
            fps = 1/(endTime-startTime)
            cv2.putText(frame,f"FPS:{fps}",(10,80),0,1,(0,255,0),2)
            return []

        # id(unique),bbox,conf,isrobot,features,
        labledResults = self.baseLabler.getLocalLabels(frame, rknnResults)

        # id(unique),estimated x/y,conf,isrobot,features,
        relativeResults = self.estimator.estimateDetectionPositions(
            frame, labledResults.copy(), self.cameraIntrinsics
        )

      

        absoluteResults = []
        for result in relativeResults:
            ((relCamX, relCamY)) = result[1]
            (
                relToRobotX,
                relToRobotY,
                relToRobotZ,
            ) = self.translator.turnCameraCoordinatesIntoRobotCoordinates(
                relCamX, relCamY, self.cameraExtrinsics
            )
            # update results with absolute position
            result[1] = (
                relToRobotX + robotPosX,
                -relToRobotY + robotPosY,  # flip y
                relToRobotZ + robotPosZ,
            )
            # note at this point these values are expected to be absolute
            # if not self.isiregularDetection(relToRobotX,relToRobotY,relToRobotZ):
            absoluteResults.append(result)
        # output is id,(absX,absY,absZ),conf,isRobot,features

        endTime = time.time()

        fps = 1/(endTime-startTime)
        cv2.putText(frame,f"FPS:{fps}",(10,80),0,1,(0,255,0),2)

        if drawBoxes:
            # draw a box with id,conf and relative estimate
            for labledResult, relativeResult in zip(labledResults, relativeResults):
                id = labledResult[0]
                bbox = labledResult[1]
                conf = labledResult[2]
                estXY = relativeResult[1]
                isRobot = labledResult[3]
                color = self.colors[id % len(self.colors)]
                cv2.rectangle(frame, bbox[0:2], bbox[2:4], color)
                cv2.putText(frame, f"Id:{id} Conf{conf} IsRobot{isRobot}", bbox[0:2], 0, 1, color)
                cv2.putText(frame, f"Relative estimate:{tuple(estXY)}", np.add(bbox[0:2],[0,30]), 0, 1, color)

        return absoluteResults

    def isiregularDetection(self, x, y, z, maxDelta=25):
        return (
            x < -maxDelta
            or x > MapConstants.fieldWidth.value + maxDelta
            or y < -maxDelta
            or y > MapConstants.fieldHeight.value + maxDelta
            or z < -maxDelta
            or z > maxDelta
        )
