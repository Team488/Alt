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



class Central:
    def __init__(self, logger : Logger):
        self.Sentinel = logger
        self.kalmanCacheRobots: KalmanCache = KalmanCache()
        self.kalmanCacheGameObjects: KalmanCache = KalmanCache()
        self.map = ProbMap()
        self.ukf = Ukf()
        self.labler = KalmanLabeler(self.kalmanCacheRobots, self.kalmanCacheGameObjects)
        self.obstacleMap = self.__tryLoadObstacleMap()
        self.pathGenerator = PathGenerator(self.map,self.obstacleMap)

    def __tryLoadObstacleMap(self):
        defaultMap = np.zeros(
            (MapConstants.fieldWidth.value, MapConstants.fieldHeight.value),dtype=bool
        )
        try:
            defaultMap = configLoader.loadNumpyConfig("obstacleMap.npy")
        except Exception as e:
            self.Sentinel.warning("obstaclemap load failed, defaulting to empty map", e)
        
        return defaultMap

    # async map update per camera, probably want to syncronize this
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
        timeStepSeconds,
        positionOffset=(0, 0, 0),
    ):
        # dissipate at start of iteration
        self.map.disspateOverTime(timeStepSeconds)
        
        
        # first get real ids

        # go through each detection and do the magic
        for singleCamResult, idOffset in cameraResults:
            if singleCamResult:
                self.labler.updateRealIds(singleCamResult, idOffset, timeStepSeconds)
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
                    self.map.addDetectedRobot(int(newState[0]), int(newState[1]), prob)
                else:
                    self.map.addDetectedGameObject(
                        int(newState[0]), int(newState[1]), prob
                    )

