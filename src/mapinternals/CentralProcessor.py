import numpy as np
import cv2
from singleton.singleton import Singleton
from mapinternals.UKF import Ukf
from tools.Constants import MapConstants, CameraIdOffsets
from mapinternals.probmap import ProbMap
from mapinternals.KalmanLabeler import KalmanLabeler
from mapinternals.KalmanCache import KalmanCache


@Singleton
class CentralProcessor:
    def __init__(self):
        self.kalmanCacheRobots: KalmanCache = KalmanCache()
        self.kalmanCacheGameObjects: KalmanCache = KalmanCache()
        self.map = ProbMap()
        self.ukf = Ukf()
        self.labler = KalmanLabeler(self.kalmanCacheRobots, self.kalmanCacheGameObjects)
        # adapt to numpys row,col by transposing
        self.obstacleMap = self.__tryLoadObstacleMap().transpose()

    def __tryLoadObstacleMap(self):
        defaultMap = np.ones(
            (MapConstants.fieldHeight.value, MapConstants.fieldWidth.value)
        )
        try:
            defaultMap = np.load("assets/obstacleMap.npy")
        except Exception as e:
            print("obstaclemap load failed, defaulting to empty map", e)
        return cv2.resize(defaultMap, self.map.getInternalSize())

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
        # first get real ids

        # go through each detection and do the magic
        for singleCamResult, idOffset in cameraResults:
            if singleCamResult:
                self.labler.updateRealIds(singleCamResult, idOffset, timeStepSeconds)
                (id, coord, prob, isRobot, features) = singleCamResult[0]
                coord = tuple(np.add(coord, positionOffset))
                (x, y, z) = coord
                # first load in to ukf, (if completely new ukf will load in as new state)
                if isRobot:
                    self.kalmanCacheRobots.LoadInKalmanData(id, x, y, self.ukf)
                else:
                    self.kalmanCacheGameObjects.LoadInKalmanData(id, x, y, self.ukf)

                newState = self.ukf.predict_and_update([x, y])
                # newState = [x,y,0,0]
                # now we have filtered data, so lets store it. First thing we do is cache the new ukf data

                if isRobot:
                    self.kalmanCacheRobots.saveKalmanData(id, self.ukf)
                else:
                    self.kalmanCacheGameObjects.saveKalmanData(id, self.ukf)
                print(tuple(newState))
                # input new estimated state into the map
                if isRobot:
                    self.map.addDetectedRobot(int(newState[0]), int(newState[1]), prob)
                else:
                    self.map.addDetectedGameObject(
                        int(newState[0]), int(newState[1]), prob
                    )

        self.map.disspateOverTime(timeStepSeconds)
