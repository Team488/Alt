import numpy as np
from mapinternals.robotTracker import RobotTracker
from Core import getLogger
from tools import UnitConversion


Sentinel = getLogger("Deep_Sort_Labler")


class DeepSortBaseLabler:
    def __init__(self, classes: list[str]) -> None:
        self.classes = classes
        # all classes are tracked independently
        self.trackers = [RobotTracker() for _ in self.classes]

    """ Returns list of tracked ids, with id, bbox, conf, class_idx, features"""

    def getLocalLabels(
        self, frame: np.ndarray, results
    ) -> list[tuple[int, tuple[int, int, int, int], float, bool, np.ndarray]]:
        trackedDetections = []
        if len(results) == 0:
            return trackedDetections

        alldetections = [[] for _ in self.classes]
        for result in results:
            (box, score, class_idx) = result
            x1, y1, x2, y2 = box
            x1 = int(x1)
            x2 = int(x2)
            y1 = int(y1)
            y2 = int(y2)
            class_idx = int(class_idx)
            detection = [x1, y1, x2, y2, score]
            if 0 <= class_idx < len(self.classes):
                alldetections[class_idx].append(detection)
            else:
                Sentinel.warning(f"Out of range class idx in results!: {class_idx}")

        for class_idx, (tracker, detections) in enumerate(
            zip(self.trackers, alldetections)
        ):
            tracker.update(frame, detections)

            for track in tracker.tracks:
                deepsort_id = track.track_id
                detection = track.currentDetection
                rawbbox = detection.to_tlbr()
                bbox = UnitConversion.toint(rawbbox)
                conf = detection.confidence
                features = detection.feature
                # x1, y1, x2, y2 = bbox
                trackedDetections.append((deepsort_id, bbox, conf, class_idx, features))

        return trackedDetections
