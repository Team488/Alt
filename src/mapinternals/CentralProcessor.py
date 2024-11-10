import numpy as np
from singleton_decorator import singleton
from mapinternals.UKF import Ukf
from tools.Constants import MapConstants, CameraIdOffsets
from mapinternals.probmap import ProbMap
from mapinternals.KalmanLabeler import KalmanLabeler
from mapinternals.KalmanCache import KalmanCache


# def addNewDetection(
#     detectionC: tuple[int, int], detectionType: DetectionType, detectionProb: float
# ):
#     # first label detection
#     mapDetection: MapDetection = KalmanLabeler.createDetection(
#         detectionC, detectionType, detectionProb
#     )  # here we would get the label in a fully boxed class MapDetection

#     # next we need to retrieve the stored kalman data for this label

#     kalmanData = KalmanCache.getData(mapDetection.detectionLabel)  # example method

#     # then we pass the new detection through the kalman filter, along with the previous data

#     (newPred, newKalmanData) = UKF.passThroughFiter(
#         mapDetection, kalmanData
#     )  # example method

#     # now you can save all this new data however needed
#     (px, py, vx, vy, etc) = newPred

#     KalmanCache.putNewInfo(newPred, newKalmanData)  # cache all new data

#     # add detection to probmap aswell
#     if DetectionType.isTypeRobot(detectionType):
#         mapWrapper.addDetectedRobot(px, py)
#     else:
#         mapWrapper.addDetectedGameObject(px, py)
@singleton
class CentralProcessor:
    def __init__(self):
        self.kalmanCacheRobots: KalmanCache = KalmanCache()
        self.kalmanCacheGameObjects: KalmanCache = KalmanCache()
        self.map = ProbMap()
        self.ukf = Ukf()
        self.labler = KalmanLabeler(self.kalmanCacheRobots, self.kalmanCacheGameObjects)

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
                # now we have filtered data, so lets store it. First thing we do is cache the new ukf data

                if isRobot:
                    self.kalmanCacheRobots.saveKalmanData(id, self.ukf)
                else:
                    self.kalmanCacheGameObjects.saveKalmanData(id, self.ukf)
                print(tuple(newState))
                # now lets also input our new estimated state into the map
                if isRobot:
                    self.map.addDetectedRobot(
                        int(newState[0]),
                        int(newState[1]),
                        prob,
                        timeStepSeconds,
                    )
                else:
                    self.map.addDetectedGameObject(
                        int(newState[0]),
                        int(newState[1]),
                        prob,
                        timeStepSeconds,
                    )

                # and now this part is done
        self.map.disspateOverTime(timeStepSeconds)
