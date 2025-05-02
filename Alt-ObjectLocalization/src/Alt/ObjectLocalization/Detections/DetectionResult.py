class DetectionResult:
    def __init__(self, bbox : tuple, conf : float, class_idx : int):
        self.bbox = bbox 
        self.conf = conf
        self.class_idx = class_idx