import numpy as np
from ultralytics import YOLO
import cv2
from abstract.inferencer import Inferencer
class ultralyticsInferencer(Inferencer):
    def __init__(
        self,
        model_path
    ):
        self.model = YOLO(model_path)


    def inferenceFrame(self, frame, drawBox=True):
        results = self.model(frame)
        if results != None and results[0] != None:
            boxes = results[0].boxes.xywh.cpu().numpy()
            half = boxes[:,2:]/2
            boxes = np.hstack((boxes[:,:2]-half,boxes[:,:2]+half))
            confs = results[0].boxes.conf.cpu()
            ids = results[0].boxes.cls.cpu()
            labels = ["algae", "coral"]
            if drawBox:
                for (bbox, conf, class_id) in zip(boxes,confs,ids):
                    x1, y1, x2, y2 = tuple(map(int,bbox))
                    cv2.rectangle(
                        img=frame,
                        pt1=(x1,y1),
                        pt2=(x2,y2),
                        color=(0, 255, 0),
                        thickness=2,
                    )
                    cv2.putText(frame, f"{labels[int(class_id)]}", (x1,y1), 1, 2, (255, 255, 255), 1)
        return results


def startDemo():
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