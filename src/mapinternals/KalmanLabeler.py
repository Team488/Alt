""" Goals for this class

    Known data: XYCoordinate of new Detection, Detection Type(Robot/Game Object), (If Robot then bumper color), and previous maps

    Goals: Take the new information given, and assign the new detection a label, this label will persist throught detections
    Ex: given new red robot detection at coord (100,121) -> figure out that this is the same robot that was at position (80,80) on the previous map. We use the SAME label so if in our cache it was called
    robot#2, then this will also be robot#2

    Expected output: A Label String that will help us know which robot is which

"""
import DetectionType
import MapDetection
import KalmanCache
from central import central
import probmap
from tools.Constants import CameraIdOffsets


class KalmanLabeler:
    def __init__(self):
        pass

    """ Replaces relative ids in list provided with their absolute id, handling new detections by trying to find old ids"""

    def getRealIds(
        self,
        singleCameraResults: list[list[int, tuple[int, int, int], float, bool]],
        cameraIdOffset: CameraIdOffsets,
        timeStepSeconds: float,
    ):
        center = central.instance()
        kalmanCacheRobots: KalmanCache = center.kalmanCacheRobots
        kalmanCacheGameObjects: KalmanCache = center.kalmanCacheGameObjects
        robotKeys: set = center.kalmanCacheRobots.getKeySet()
        gameObjectKeys: set = center.kalmanCacheGameObjects.getKeySet()
        newDetections = ()

        for singleCameraResult in singleCameraResults:
            singleCameraResult[0] += cameraIdOffset.getIdOffset()  # adjust id
            (realId, (x, y, z), conf, isRobot) = singleCameraResult
            cacheOfChoice: KalmanCache = (
                kalmanCacheRobots if isRobot else kalmanCacheGameObjects
            )
            keySetOfChoice = robotKeys if isRobot else gameObjectKeys
            data = cacheOfChoice.getSavedKalmanData(realId)
            if data is None:
                newDetections.append(singleCameraResult)
            else:
                # we want to isolate entries not seen
                keySetOfChoice.remove(realId)

        for newDetection in newDetections:
            (realId, (x, y, z), conf, isRobot) = newDetection
            keySetOfChoice = robotKeys if isRobot else gameObjectKeys
            cacheOfChoice: KalmanCache = (
                kalmanCacheRobots if isRobot else kalmanCacheGameObjects
            )

            for key in keySetOfChoice[:]:
                kalmanEntry = cacheOfChoice.get(key)
