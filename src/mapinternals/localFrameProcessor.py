import random
from ultralytics import YOLO
from mapinternals.deepSortBaseLabler import DeepSortBaseLabler
from tools.Constants import CameraIntrinsics, CameraExtrinsics
from tools.positionEstimator import PositionEstimator
from tools.positionTranslations import CameraToRobotTranslator
from coreinterface.CoreInput import getRobotPosition
import numpy as np
import cv2

""" This handles the full pipline from a frame to detections with deepsort id's. You can think of it as the local part of the detection pipeline
    After this detections are centralized over the network to an orin and thats where the Ukf and etc will reside
"""


class LocalFrameProcessor:
    def __init__(
        self, cameraIntrinsics: CameraIntrinsics, cameraExtrinsics: CameraExtrinsics
    ) -> None:
        self.baseLabler: DeepSortBaseLabler = DeepSortBaseLabler()
        self.cameraIntrinsics: CameraIntrinsics = cameraIntrinsics
        self.cameraExtrinsics: CameraExtrinsics = cameraExtrinsics
        self.model = YOLO("assets/bestV8.pt")  # Open the model
        self.estimator = PositionEstimator()
        self.translator = CameraToRobotTranslator()
        self.colors = [
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for j in range(15)
        ]

    def processFrame(
        self, frame, drawBoxes=True
    ) -> list[list[int, tuple[int, int, int], float, bool, np.ndarray]]:
        results = self.model.predict(frame, show_boxes=False, conf=0.8, show=False)
        labledResults = self.baseLabler.getLocalLabels(frame, results)
        if drawBoxes:
            for result in labledResults:
                id = result[0]
                bbox = result[1]
                print(bbox)
                color = self.colors[id % len(self.colors)]
                cv2.rectangle(frame, bbox[0:2], bbox[2:4], color)
                cv2.putText(frame, f"Id:{id}", bbox[0:2], 0, 2, color)
        # id(unique),features,estimated x/y,conf,isrobot
        relativeResults = self.estimator.estimateDetectionPositions(
            frame, labledResults, self.cameraIntrinsics
        )
        robotPosX, robotPosY, robotPosZ = getRobotPosition()
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
                relToRobotY + robotPosY,
                relToRobotZ + robotPosZ,
            )
        # output is id,(absX,absY,absZ),conf,isRobot,features
        return relativeResults
