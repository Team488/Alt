import numpy as np
import cv2
from logging import Logger
from mapinternals.UKF import Ukf
from tools import configLoader
from tools.Constants import MapConstants, CameraIdOffsets
from mapinternals.probmap import ProbMap
from mapinternals.KalmanLabeler import KalmanLabeler
from mapinternals.KalmanCache import KalmanCache
from pathplanning.PathGenerator import PathGenerator
from reefTracking.ReefState import ReefState
from Core.ConfigOperator import ConfigOperator
from Core.PropertyOperator import PropertyOperator


class Central:
    def __init__(
        self, logger: Logger, configOp: ConfigOperator, propertyOp: PropertyOperator
    ):
        self.Sentinel = logger
        self.configOp = configOp
        self.propertyOp = propertyOp

        self.useObstacles = self.propertyOp.createProperty("Use_Obstacles", True)

        self.kalmanCacheRobots: KalmanCache = KalmanCache()
        self.kalmanCacheGameObjects: KalmanCache = KalmanCache()
        self.objectmap = ProbMap()
        self.reefState = ReefState()
        self.ukf = Ukf()
        self.labler = KalmanLabeler(self.kalmanCacheRobots, self.kalmanCacheGameObjects)
        self.obstacleMap = self.__tryLoadObstacleMap()
        self.pathGenerator = PathGenerator(self.objectmap, self.obstacleMap)

    def __tryLoadObstacleMap(self):
        defaultMap = np.zeros(
            (MapConstants.fieldWidth.value, MapConstants.fieldHeight.value), dtype=bool
        )
        if self.useObstacles.get():
            obstacleMap = self.configOp.getContent("obstacleMap.npy")
            if obstacleMap is not None:
                return obstacleMap
            else:
                # this will never happen, as we have the obstaclemap in assets too
                self.Sentinel.warning(
                    "Failed to load obstacles, defaulting to empty map"
                )

        return defaultMap

    def processReefUpdate(
        self,
        reefResults: tuple[list[tuple[int, int, float]], list[tuple[int, float]]],
        timeStepMs,
    ):
        self.reefState.dissipateOverTime(timeStepMs)

        for reefResult in reefResults:
            print(reefResult)
            coralObservation, algaeObservation = reefResult
            for apriltagid, branchid, opennessconfidence in coralObservation:
                self.reefState.addObservationCoral(
                    apriltagid, branchid, opennessconfidence
                )

            for apriltagid, opennessconfidence in algaeObservation:
                self.reefState.addObservationAlgae(apriltagid, opennessconfidence)

    def processFrameUpdate(
        self,
        cameraResults: list[
            tuple[
                list[
                    list[int, tuple[int, int, int], float, bool, np.ndarray],
                    CameraIdOffsets,
                ]
            ]
        ],
        timeStepMs,
        positionOffset=(0, 0, 0),
    ):
        # dissipate at start of iteration
        self.objectmap.disspateOverTime(timeStepMs)

        # first get real ids

        # go through each detection and do the magic
        for singleCamResult, idOffset in cameraResults:
            if singleCamResult:
                self.labler.updateRealIds(singleCamResult, idOffset, timeStepMs)
                (id, coord, prob, isRobot, features) = singleCamResult[0]
                # todo add feature deduping here
                coord = tuple(np.add(coord, positionOffset))
                (x, y, z) = coord
                # first load in to ukf, (if completely new ukf will load in as new state)
                if isRobot:
                    self.kalmanCacheRobots.LoadInKalmanData(id, x, y, self.ukf)
                else:
                    self.kalmanCacheGameObjects.LoadInKalmanData(id, x, y, self.ukf)

                newState = self.ukf.predict_and_update([x, y])

                # now we have filtered data, so lets store it. First thing we do is cache the new ukf data

                if isRobot:
                    self.kalmanCacheRobots.saveKalmanData(id, self.ukf)
                else:
                    self.kalmanCacheGameObjects.saveKalmanData(id, self.ukf)
                # input new estimated state into the map
                if isRobot:
                    self.objectmap.addDetectedRobot(
                        int(newState[0]), int(newState[1]), prob
                    )
                else:
                    self.objectmap.addDetectedGameObject(
                        int(newState[0]), int(newState[1]), prob
                    )
