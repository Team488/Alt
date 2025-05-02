import numpy as np
from ultralytics import YOLO
import cv2

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


def startDemo() -> None:
    from inference.MultiInferencer import MultiInferencer
    from tools.Constants import InferenceMode

    inf = MultiInferencer(inferenceMode=InferenceMode.ULTRALYTICSMED2025)
    cap = cv2.VideoCapture("assets/reefscapevid.mp4")

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            results = inf.run(frame, 0.7, drawBoxes=True)
            cv2.imshow("ultralytics", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    startDemo()
