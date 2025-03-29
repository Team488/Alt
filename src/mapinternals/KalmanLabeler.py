""" Goals for this class

    Known data: XYCoordinate of new Detection, Detection Type(Robot/Game Object), (If Robot then bumper color), and previous maps

    Goals: Take the new information given, and assign the new detection a label, this label will persist throught detections
    Ex: given new red robot detection at coord (100,121) -> figure out that this is the same robot that was at position (80,80) on the previous map. We use the SAME label so if in our cache it was called
    robot#2, then this will also be robot#2

    Expected output: A Label String that will help us know which robot is which

"""
import numpy as np
from mapinternals.KalmanCache import KalmanCache
from mapinternals.KalmanEntry import KalmanEntry
from tools.Constants import CameraIdOffsets2024, LabelingConstants, Label
from tools import Calculator
from Core import getChildLogger

Sentinel = getChildLogger("Kalman_Labler")


class KalmanLabeler:
    def __init__(self, kalmanCaches: list[KalmanCache], labels: list[Label]) -> None:
        self.kalmanCaches = kalmanCaches
        self.labels = labels

    """ Replaces relative ids in list provided with their absolute id, handling new detections by trying to find old ids"""

    def updateRealIds(
        self,
        singleCameraResults: list[
            list[int, tuple[int, int, int], float, int, np.ndarray]
        ],
        cameraIdOffset: int,
        timeStepSeconds: float,
    ) -> None:
        allkeys: list[set] = [cache.getKeySet() for cache in self.kalmanCaches]
        allmarkedIndexs = [[] for _ in range(len(self.kalmanCaches))]

        for i in range(len(singleCameraResults)):
            singleCameraResult = singleCameraResults[i]
            singleCameraResult[0] += cameraIdOffset
            # adjust id by a fixed camera offset, so that id collisions dont happen
            (realId, (x, y, z), conf, class_idx, features) = singleCameraResult

            if class_idx < 0 or class_idx > len(self.kalmanCaches):
                Sentinel.warning(
                    f"Update real ids got invalid class_idx! : {class_idx}"
                )
                continue
            cache = self.kalmanCaches[class_idx]
            keySetOfChoice = allkeys[class_idx]
            data = cache.getSavedKalmanData(realId)

            if data is None:
                allmarkedIndexs[class_idx].append(i)
            else:
                # we want to isolate entries not seen
                keySetOfChoice.remove(realId)

        # iterate over remaining keys to see if any of the new detections are within a delta and match
        # todo add robot color as a matching factor

        for markedIndexs, keys, cache in zip(
            allmarkedIndexs, allkeys, self.kalmanCaches
        ):
            for index in markedIndexs:
                (realId, (x, y, z), conf, class_idx, features) = singleCameraResults[
                    index
                ]

                closestId = None
                closestDistance = 100000
                # todo optimize use rectangle segments
                for key in keys:
                    kalmanEntry: KalmanEntry = cache.getSavedKalmanData(key)
                    # right now i am trying to find a match by finding the closest entry and seeing if its within a maximum delta
                    [oldX, oldY, vx, vy] = kalmanEntry.X
                    maxRange = (
                        Calculator.calculateMaxRange(
                            vx, vy, timeStepSeconds, self.labels[class_idx]
                        )
                        + 0.05
                    )
                    objectRange = Calculator.getDistance(
                        x, y, oldX, oldY, vx, vy, timeStepSeconds
                    )
                    if objectRange < maxRange and objectRange < closestDistance:
                        closestId = key
                        closestDistance = objectRange

                if closestId is not None:
                    # found match within range
                    # remove id from possible options and update result entry
                    singleCameraResults[index][0] = closestId
                    keySetOfChoice.remove(closestId)

        for keys, cache in zip(allkeys, self.kalmanCaches):
            for remainingKey in keys:
                out = cache.getSavedKalmanData(remainingKey)
                out.incrementNotSeen()
                if out.framesNotSeen > LabelingConstants.MAXFRAMESNOTSEEN.value:
                    # too many frames being not seen
                    cache.removeKalmanEntry(remainingKey)
