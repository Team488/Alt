import numpy as np
from Alt.Core import getChildLogger
from Alt.Core.Units import Conversions

from ..Detections.DetectionResult import DetectionResult
from ..Tracking.TrackedDetectionResult import TrackedDetectionResult
from .robotTracker import RobotTracker

Sentinel = getChildLogger("Deep_Sort_Labler")

class DeepSortBaseLabler:
    def __init__(self, nClasses: int) -> None:
        self.nClasses = nClasses
        # all classes are tracked independently
        self.trackers = [RobotTracker() for _ in range(self.nClasses)]

    """ Returns list of tracked ids, with id, bbox, conf, class_idx, features"""

    def labelResults(
        self, frame: np.ndarray, results : list[DetectionResult]
    ) -> list[TrackedDetectionResult]:
        # nothing to track
        trackedDetections = []
        if len(results) == 0:
            return trackedDetections

        # initalize tracker detections
        alldetections = [[] for _ in range(self.nClasses)]
        for result in results:
            x1, y1, x2, y2 = Conversions.toint(result.bbox)
            class_idx = int(result.class_idx)
            detection = [x1, y1, x2, y2, result.conf]

            if 0 <= class_idx < self.nClasses:
                alldetections[class_idx].append(detection)
            else:
                Sentinel.warning(f"Out of range class idx in results!: {class_idx}")

        # go over every tracker and update it
        for class_idx, (tracker, detections) in enumerate(
            zip(self.trackers, alldetections)
        ):
            tracker.update(frame, detections)

            for track in tracker.tracks:
                deepsort_id = track.track_id
                detection = track.currentDetection
                rawbbox = detection.to_tlbr()
                bbox = Conversions.toint(rawbbox)
                conf = detection.confidence
                features = detection.feature
                trackedDetections.append(TrackedDetectionResult(bbox, conf, class_idx, deepsort_id, features))

        return trackedDetections
