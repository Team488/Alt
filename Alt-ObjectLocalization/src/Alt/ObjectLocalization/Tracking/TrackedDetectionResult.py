import numpy as np

from ..Detections.DetectionResult import DetectionResult

class TrackedDetectionResult(DetectionResult):
    def __init__(self, bbox : tuple, conf : float, class_idx : int, deepsort_id : int, features : np.ndarray):
        super().__init__(bbox, conf, class_idx)
        self.deepsort_id = deepsort_id
        self.features = features
