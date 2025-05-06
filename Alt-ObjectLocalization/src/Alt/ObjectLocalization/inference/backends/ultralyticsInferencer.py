import numpy as np
from ultralytics import YOLO

from ..inferencerBackend import InferencerBackend
from ...Detections.DetectionResult import DetectionResult

class ultralyticsInferencer(InferencerBackend):
    def initialize(self) -> None:
        self.model = YOLO(self.modelConfig.getPath())

    def preprocessFrame(self, frame):
        return frame

    def runInference(self, inputTensor):
        return self.model(inputTensor)

    def postProcessBoxes(self, results, frame, minConf) -> list[DetectionResult]:
        if results != None and results[0] != None:
            boxes = results[0].boxes.xywh.cpu().numpy()
            half = boxes[:, 2:] / 2
            boxes = np.hstack((boxes[:, :2] - half, boxes[:, :2] + half))
            confs = results[0].boxes.conf.cpu()
            ids = results[0].boxes.cls.cpu().numpy().astype(int)
            
            return [DetectionResult(result[0], result[1], result[2]) for result in zip(boxes, confs, ids) if result[2] > minConf]

        return []