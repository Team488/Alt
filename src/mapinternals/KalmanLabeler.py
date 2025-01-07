""" Goals for this class

    Known data: XYCoordinate of new Detection, Detection Type(Robot/Game Object), (If Robot then bumper color), and previous maps

    Goals: Take the new information given, and assign the new detection a label, this label will persist throught detections
    Ex: given new red robot detection at coord (100,121) -> figure out that this is the same robot that was at position (80,80) on the previous map. We use the SAME label so if in our cache it was called
    robot#2, then this will also be robot#2

    Expected output: A Label String that will help us know which robot is which

"""
from mapinternals.KalmanCache import KalmanCache
from mapinternals.KalmanEntry import KalmanEntry
from tools.Constants import CameraIdOffsets, LabelingConstants
from tools import Calculator


class KalmanLabeler:
    def __init__(
        self, kalmanCacheRobots: KalmanCache, kalmanCacheGameObjects: KalmanCache
    ):
        self.kalmanCacheRobots: KalmanCache = kalmanCacheRobots
        self.kalmanCacheGameObjects: KalmanCache = kalmanCacheGameObjects
        pass

    """ Replaces relative ids in list provided with their absolute id, handling new detections by trying to find old ids"""

    def updateRealIds(
        self,
        singleCameraResults: list[list[int, tuple[int, int, int], float, bool]],
        cameraIdOffset: CameraIdOffsets,
        timeStepSeconds: float,
    ):
        robotKeys: set = self.kalmanCacheRobots.getKeySet()
        gameObjectKeys: set = self.kalmanCacheGameObjects.getKeySet()
        markedIndexs = []
        for i in range(len(singleCameraResults)):
            singleCameraResult = singleCameraResults[i]
            singleCameraResult[0] += cameraIdOffset.getIdOffset()
            # adjust id by a fixed camera offset, so that id collisions dont happen
            (realId, (x, y, z), conf, isRobot) = singleCameraResult[:4]
            cacheOfChoice: KalmanCache = self.kalmanCacheRobots if isRobot else self.kalmanCacheGameObjects
            keySetOfChoice = robotKeys if isRobot else gameObjectKeys
            data = cacheOfChoice.getSavedKalmanData(realId)
            if data is None:
                markedIndexs.append(i)
            else:
                # we want to isolate entries not seen
                keySetOfChoice.remove(realId)

        # iterate over remaining robot and gameobject keys to see if any of the new detections are within a delta and match
        # todo add robot color as a matching factor

        for index in markedIndexs:
            (realId, (detectionX, detectionY, z), conf, isRobot) = singleCameraResults[index][:4]
            keySetOfChoice = robotKeys if isRobot else gameObjectKeys
            cacheOfChoice: KalmanCache = (
                self.kalmanCacheRobots if isRobot else self.kalmanCacheGameObjects
            )

            closestId = None
            closestDistance = 100000
            # todo optimize use rectangle segments
            for key in keySetOfChoice:
                kalmanEntry: KalmanEntry = cacheOfChoice.getSavedKalmanData(key)
                # right now i am trying to find a match by finding the closest entry and seeing if its within a maximum delta
                [oldX, oldY, vx, vy] = kalmanEntry.X
                maxRange = (
                    Calculator.calculateMaxRange(vx, vy, timeStepSeconds, isRobot)
                    + 0.05
                )
                objectRange = Calculator.getDistance(
                    detectionX, detectionY, oldX, oldY, vx, vy, timeStepSeconds
                )
                if objectRange < maxRange and objectRange < closestDistance:
                    closestId = key
                    closestDistance = objectRange

            if closestId is not None:
                # found match within range
                # remove id from possible options and update result entry
                singleCameraResults[index][0] = closestId
                keySetOfChoice.remove(closestId)
        
        for remainingKey in robotKeys:
            out: KalmanEntry = self.kalmanCacheRobots.getSavedKalmanData(remainingKey)
            out.incrementNotSeen()
            if out.framesNotSeen > LabelingConstants.MAXFRAMESNOTSEEN.value:
                self.kalmanCacheRobots.removeKalmanEntry(remainingKey)

        for remainingKey in gameObjectKeys:
            out: KalmanEntry = self.kalmanCacheGameObjects.getSavedKalmanData(
                remainingKey
            )
            out.incrementNotSeen()
            if out.framesNotSeen > LabelingConstants.MAXFRAMESNOTSEEN.value:
                self.kalmanCacheGameObjects.removeKalmanEntry(remainingKey)
