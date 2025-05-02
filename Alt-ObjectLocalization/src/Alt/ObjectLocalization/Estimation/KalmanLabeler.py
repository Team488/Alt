import numpy as np

from Alt.Core import getChildLogger

from .KalmanCache import KalmanCache
from ..Constants.Kalman import LabelingConstants
from ..Localization.LocalizationResult import DeviceLocalizationResult

Sentinel = getChildLogger("Kalman_Labler")


class KalmanLabeler:
    def __init__(self, kalmanCaches: list[KalmanCache], nClasses: int, idOffset: int = 30) -> None:
        self.kalmanCaches = kalmanCaches
        self.nClasses = nClasses
        self.idOffsets = {}
        self.idStart = 0
        self.idOffset = idOffset

    """ Replaces relative ids in list provided with their absolute id, handling new detections by trying to find old ids"""

    def updateRealIds(
        self,
        deviceResult: DeviceLocalizationResult,
        timeStepMs: float,
    ) -> None:
        # get or create a id offset for this device
        uuid = deviceResult.deviceUniqueName
        if uuid in self.idOffsets:
            offset = self.idOffsets.get(uuid)
        else:
            offset = self.idStart
            self.idStart += self.idOffset
            self.idOffsets[uuid] = offset

        # initialize containers for id reassignment
        allkeys: list[set] = [cache.getKeySet() for cache in self.kalmanCaches]
        allmarkedIndexs : list[list[int]] = [[] for _ in range(self.nClasses)]

        for idx, localizationResult in enumerate(deviceResult.localizedResults):
            # adjust id by the fixed camera offset, so that id collisions dont happen
            localizationResult.deepsort_id += offset

            if localizationResult.class_idx < 0 or localizationResult.class_idx >= self.nClasses:
                Sentinel.warning(
                    f"Update real ids got invalid class_idx! : {localizationResult.class_idx}"
                )
                continue

            cache = self.kalmanCaches[localizationResult.class_idx]
            keySetOfChoice = allkeys[localizationResult.class_idx]
            data = cache.getSavedKalmanData(localizationResult.deepsort_id)

            if data is None:
                # mark it as a missing entry
                allmarkedIndexs[localizationResult.class_idx].append(idx)
            else:
                # remove from available optios
                keySetOfChoice.remove(localizationResult.deepsort_id)

        # iterate over remaining keys to see if any of the new detections are within a delta and match
        # todo add robot color as a matching factor

        for markedIndexs, keys, cache in zip(
            allmarkedIndexs, allkeys, self.kalmanCaches
        ):
            for index in markedIndexs:
                localizationResult = deviceResult.localizedResults[index]

                closestId : int = None
                closestDistance = 1e5
                # todo optimize using some sort of binary segmentation
                # also very important, consider using direction of vx,vy to influence the range to become warped in the direction of vx/vy
                # when considering an object that can change direction very quickly its less of an issue but consider a rolling object like a ball.
                for key in keys:
                    kalmanEntry = cache.getSavedKalmanData(key)

                    oldX, oldY, vx, vy = kalmanEntry.X
                    maxRange = timeStepMs * np.linalg.norm([vx, vy])
                    dist = np.linalg.norm([localizationResult.location.x - oldX, localizationResult.location.y - oldY])

                    if dist <= maxRange and dist < closestDistance:
                        closestId = key
                        closestDistance = dist

                if closestId is not None:
                    # found match within range
                    # remove id from possible options and update result entry
                    localizationResult.deepsort_id = closestId
                    keys.remove(closestId)

        # handle any remanining keys
        for keys, cache in zip(allkeys, self.kalmanCaches):
            for remainingKey in keys:
                out = cache.getSavedKalmanData(remainingKey)
                out.incrementNotSeen()
                if out.framesNotSeen > LabelingConstants.MAXFRAMESNOTSEEN.value:
                    # too many frames being not seen
                    cache.removeKalmanEntry(remainingKey)