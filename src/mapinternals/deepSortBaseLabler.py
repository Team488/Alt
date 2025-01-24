import numpy as np
from mapinternals.robotTracker import RobotTracker


class DeepSortBaseLabler:
    def __init__(self) -> None:
        self.trackerL1 = RobotTracker()
        self.trackerL2 = RobotTracker()

    """ Returns list of tracked ids, with id, bbox, conf, isRobot,features"""

    def getLocalLabels(
        self, frame, results
    ) -> list[tuple[int, tuple[int, int, int, int], float, bool, np.ndarray]]:
        trackedDetections = []
        if len(results) == 0:
            return trackedDetections
        detectionsGameObjects = []
        detectionsRobots = []
        for result in results:
            (box, score, class_id) = result
            x1, y1, x2, y2 = box
            x1 = int(x1)
            x2 = int(x2)
            y1 = int(y1)
            y2 = int(y2)
            class_id = int(class_id)
            detection = [x1, y1, x2, y2, score]
            if class_id == 0:  # robot or algae
                detectionsRobots.append(detection)
            else:
                detectionsGameObjects.append(detection)
        self.trackerL1.update(frame, detectionsGameObjects)
        self.trackerL2.update(frame, detectionsRobots)
        for track in self.trackerL2.tracks:
            detection = track.currentDetection
            rawbbox = detection.to_tlbr()  # todo make this tlwh
            bbox = (
                int(rawbbox[0]),
                int(rawbbox[1]),
                int(rawbbox[2]),
                int(rawbbox[3]),
            )
            conf = detection.confidence
            features = detection.feature
            # x1, y1, x2, y2 = bbox
            trackedDetections.append((track.track_id, bbox, conf, True, features))
        for track in self.trackerL1.tracks:
            detection = track.currentDetection
            rawbbox = detection.to_tlbr()  # todo make this tlwh
            bbox = (
                int(rawbbox[0]),
                int(rawbbox[1]),
                int(rawbbox[2]),
                int(rawbbox[3]),
            )
            conf = detection.confidence
            features = detection.feature
            # x1, y1, x2, y2 = bbox
            trackedDetections.append((track.track_id, bbox, conf, False, features))
        return trackedDetections
