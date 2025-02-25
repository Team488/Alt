import numpy as np
from ultralytics import YOLO
import cv2
from abstract.inferencerBackend import InferencerBackend


class ultralyticsInferencer(InferencerBackend):
    def initialize(self) -> None:
        self.model = YOLO(self.mode.getModelPath())

    def preprocessFrame(self, frame):
        return frame

    def runInference(self, inputTensor):
        return self.model(inputTensor)

    def postProcess(self, results, frame, minConf):
        if results != None and results[0] != None:
            boxes = results[0].boxes.xywh.cpu().numpy()
            half = boxes[:, 2:] / 2
            boxes = np.hstack((boxes[:, :2] - half, boxes[:, :2] + half))
            confs = results[0].boxes.conf.cpu()
            ids = results[0].boxes.cls.cpu().numpy().astype(int)
            # TODO add minconf here
            return list(zip(boxes, confs, ids))

        return []


def startDemo() -> None:
    video_path = "assets/reefscapevid.mp4"
    cap = cv2.VideoCapture(video_path)
    inferencer = ultralyticsInferencer("assets/2025-best-151.pt")
    # Check if the video opened successfully
    if not cap.isOpened():
        print("Error: Could not open video.")
        exit()

    cap.set(cv2.CAP_PROP_POS_FRAMES, 500)

    # Process each frame
    while True:
        ret, frame = cap.read()
        if ret:
            inferencer.inferenceFrame(frame, drawBox=True)
            cv2.imshow("frame", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows()
    cap.release


if __name__ == "__main__":
    startDemo()
