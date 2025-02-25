import random
import time
import cv2
import numpy as np
from mapinternals.deepSortBaseLabler import DeepSortBaseLabler
from tools import UnitConversion
from tools.Constants import (
    CameraIntrinsics,
    CameraExtrinsics,
    MapConstants,
    InferenceMode,
    ConfigConstants,
)
from tools.Units import UnitMode
from tools.positionEstimator import PositionEstimator
from tools.positionTranslations import CameraToRobotTranslator, transformWithYaw
from inference.MultiInferencer import MultiInferencer
from Core import getLogger


Sentinel = getLogger("Local_Frame_Processor")


class LocalFrameProcessor:
    """This handles the full pipline from a frame to detections with deepsort id's. You can think of it as the local part of the detection pipeline
    After this detections are centralized over the network to an orin and thats where the Ukf and etc will reside
    """

    def __init__(
        self,
        cameraIntrinsics: CameraIntrinsics,
        cameraExtrinsics: CameraExtrinsics,
        inferenceMode: InferenceMode,
        isSimulationMode=False,
        tryOCR=False,
    ) -> None:
        self.inf = self.createInferencer(inferenceMode)
        self.inferenceMode = inferenceMode
        self.labels = self.inferenceMode.getLabelsAsStr()
        self.baseLabler: DeepSortBaseLabler = DeepSortBaseLabler(
            inferenceMode.getLabelsAsStr()
        )
        self.cameraIntrinsics: CameraIntrinsics = cameraIntrinsics
        self.cameraExtrinsics: CameraExtrinsics = cameraExtrinsics
        self.estimator = PositionEstimator(
            isSimulationMode=isSimulationMode, tryocr=tryOCR
        )
        self.translator = CameraToRobotTranslator()
        self.colors = [
            (random.randint(0, 255), random.randint(0, 255), random.randint(0, 255))
            for _ in range(15)
        ]

    def createInferencer(self, inferenceMode: InferenceMode):
        Sentinel.info("Creating inferencer: " + inferenceMode.getName())
        return MultiInferencer(inferenceMode)

    def processFrame(
        self,
        frame,
        robotPosXCm=0,
        robotPosYCm=0,
        robotPosZCm=0,
        robotYawRad=0,
        drawBoxes=False,
        useAbsolutePosition=True,
        customCameraExtrinsics: CameraExtrinsics = None,
        customCameraIntrinsics: CameraIntrinsics = None,
        maxDetections=None,
    ) -> list[list[int, tuple[int, int, int], float, bool, np.ndarray]]:
        """output is list of id,(absX,absY,absZ),conf,isRobot,features"""
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
        yoloResults = self.inf.run(
            frame, minConf=ConfigConstants.confThreshold, drawBoxes=False
        )  # we will draw deepsort tracked boxes instead
        if maxDetections != None:
            yoloResults = yoloResults[:maxDetections]

        if len(yoloResults) == 0:
            if drawBoxes:
                endTime = time.time()
                fps = 1 / (endTime - startTime)
                cv2.putText(frame, f"FPS:{fps}", (10, 20), 0, 1, (0, 255, 0), 2)
            return []

        # id(unique),bbox,conf,isrobot,features,
        labledResults = self.baseLabler.getLocalLabels(frame, yoloResults)

        if drawBoxes:
            # draw a box with id,conf and relative estimate
            for labledResult in labledResults:
                id = labledResult[0]
                bbox = labledResult[1]
                conf = labledResult[2]
                classId = labledResult[3]

                label = "INVALID"  # technically redundant, as the deepsort step filters out any invalid class_idxs
                if 0 <= classId < len(self.labels):
                    label = self.labels[classId]

                color = self.colors[id % len(self.colors)]
                cv2.rectangle(frame, bbox[0:2], bbox[2:4], color)
                cv2.putText(
                    frame,
                    f"Id:{id} Conf{conf:.2f} Label: {label}",
                    UnitConversion.toint(np.add(bbox[:2], bbox[2:4]), 2),
                    0,
                    1,
                    color,
                    1,
                )

        # id(unique),estimated x/y,conf,class_idx,features,
        relativeResults = self.estimator.estimateDetectionPositions(
            frame, labledResults.copy(), camIntrinsics, self.inferenceMode
        )

        # print(f"{robotPosXCm=} {robotPosYCm=} {robotYawRad=}")
        if useAbsolutePosition:
            finalResults = []
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
                absx, absy, absz = result[1]
                if not self.isiregularDetection(absx, absy, absz):
                    finalResults.append(result)
                else:
                    Sentinel.warning("Iregular Detection!:")
                    Sentinel.debug(f"{absx =} {absy =} {absz =}")
                    Sentinel.debug(f"{relToRobotX =} {relToRobotY =} {relToRobotZ =}")

        else:
            for result in relativeResults:
                result[1].append(0)  # add z component
            finalResults = relativeResults

        # output is id,(absX,absY,absZ),conf,class_idx,features

        endTime = time.time()

        fps = 1 / (endTime - startTime)

        if drawBoxes:
            # add final fps
            cv2.putText(frame, f"FPS:{fps}", (10, 20), 0, 1, (0, 255, 0), 2)

        return finalResults

    def isiregularDetection(self, x, y, z):  # cm
        return (
            x < 0
            or x >= MapConstants.fieldWidth.value
            or y < 0
            or y >= MapConstants.fieldHeight.value
            # or z < -maxDelta
            # or z > maxDelta
        )
