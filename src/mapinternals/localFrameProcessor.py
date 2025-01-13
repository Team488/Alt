import random
import time
from mapinternals.deepSortBaseLabler import DeepSortBaseLabler
from tools.Constants import CameraIntrinsics, CameraExtrinsics, MapConstants, UnitMode
from tools.positionEstimator import PositionEstimator
from tools.positionTranslations import CameraToRobotTranslator, transformWithYaw
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
        unitMode: UnitMode,
        useRknn=False,
        isSimulationMode = False,
        tryOCR = False
    ) -> None:
        self.unitMode = unitMode
        if useRknn:
            from inference.rknnInferencer import rknnInferencer

            self.inf = rknnInferencer()
        else:
            from inference.onnxInferencer import onnxInferencer
            self.inf = onnxInferencer()
        self.baseLabler: DeepSortBaseLabler = DeepSortBaseLabler()
        self.cameraIntrinsics: CameraIntrinsics = cameraIntrinsics
        self.cameraExtrinsics: CameraExtrinsics = cameraExtrinsics
        self.estimator = PositionEstimator(isSimulationMode=isSimulationMode,tryocr=tryOCR)
        self.translator = CameraToRobotTranslator()
        self.colors = [
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for _ in range(15)
        ]

    # output is list of id,(absX,absY,absZ),conf,isRobot,features
    def processFrame(
        self,
        frame,
        robotPosXCm=0,
        robotPosYCm=0,
        robotPosZCm=0,
        robotYawRad=0,
        drawBoxes=False,
        customCameraExtrinsics=None,
        customCameraIntrinsics=None,
        maxDetections=None,
    ) -> list[list[int, tuple[int, int, int], float, bool, np.ndarray]]:
        camIntrinsics = (
            customCameraIntrinsics
            if customCameraIntrinsics is not None
            else self.cameraIntrinsics
        )
        camExtrinsics = (
            customCameraExtrinsics
            if customCameraExtrinsics is not None
            else self.cameraExtrinsics
        )
        startTime = time.time()
        yoloResults = self.inf.inferenceFrame(frame)
        if maxDetections != None:
            yoloResults = yoloResults[:maxDetections]

        if len(yoloResults) == 0:
            if drawBoxes:
                endTime = time.time()
                fps = 1 / (endTime - startTime)
                cv2.putText(frame, f"FPS:{fps}", (10, 80), 0, 1, (0, 255, 0), 2)
            return []

        # id(unique),bbox,conf,isrobot,features,
        labledResults = self.baseLabler.getLocalLabels(frame, yoloResults)

        if drawBoxes:
            # draw a box with id,conf and relative estimate
            for labledResult in labledResults:
                id = labledResult[0]
                bbox = labledResult[1]
                conf = labledResult[2]
                isRobot = labledResult[3]
                color = self.colors[id % len(self.colors)]
                cv2.rectangle(frame, bbox[0:2], bbox[2:4], color)
                cv2.putText(
                    frame,
                    f"Id:{id} Conf{conf:.2f} IsRobot{isRobot}",
                    (10, 30),
                    0,
                    1,
                    color,
                    1,
                )

        # id(unique),estimated x/y,conf,isrobot,features,
        relativeResults = self.estimator.estimateDetectionPositions(
            frame, labledResults.copy(), camIntrinsics
        )

        # print(f"{robotPosXCm=} {robotPosYCm=} {robotYawRad=}")
        absoluteResults = []
        for result in relativeResults:
            ((relCamX, relCamY)) = result[1]
            (
                relToRobotX,
                relToRobotY,
                relToRobotZ,
            ) = self.translator.turnCameraCoordinatesIntoRobotCoordinates(
                relCamX, relCamY, camExtrinsics
            )
            # factor in robot orientation
            result[1] = transformWithYaw(
                np.array([relToRobotX, relToRobotY, relToRobotZ]), robotYawRad
            )
            # update results with absolute position
            result[1] = np.add(
                result[1], np.array([robotPosXCm, robotPosYCm, robotPosZCm])
            )

            # note at this point these values are expected to be absolute

            # if not self.isiregularDetection(relToRobotX,relToRobotY,relToRobotZ):
            absoluteResults.append(result)
        # output is id,(absX,absY,absZ),conf,isRobot,features

        endTime = time.time()

        fps = 1 / (endTime - startTime)

        if drawBoxes:
            # cv2.putText(frame,f"FPS:{fps}",(10,80),0,1,(0,255,0),2)
            # print(f"FPS:{fps}")
            # draw a box with id,conf and relative estimate
            for labledResult, relativeResult in zip(labledResults, relativeResults):
                id = labledResult[0]
                bbox = labledResult[1]
                conf = labledResult[2]
                estXYZ = relativeResult[1]
                isRobot = labledResult[3]
                color = self.colors[id % len(self.colors)]
                cv2.rectangle(frame, bbox[0:2], bbox[2:4], color)
                cv2.putText(
                    frame,
                    f"Id:{id} Conf{conf:.2f} IsRobot{isRobot}",
                    (10, 30),
                    0,
                    1,
                    color,
                    1,
                )
                cv2.putText(
                    frame,
                    f"Absolute estimate:{tuple(map(lambda x: round(x, 2),estXYZ))}",
                    (10, 100),
                    0,
                    1,
                    color,
                    1,
                )

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
