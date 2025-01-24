import os
import time
import cv2
import numpy as np
from rknnlite.api import RKNNLite
from inference import utils
from abstract.inferencer import Inferencer
from tools.Constants import ConfigConstants


class rknnInferencer(Inferencer):
    def __init__(self, model_path):
        # export needed rknpu .so
        so_path = os.getcwd() + "/assets/"

        os.environ[
            "LD_LIBRARY_PATH"
        ] = f"{so_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"

        # Check if LD_LIBRARY_PATH is set correctly
        print("LD_LIBRARY_PATH:", os.environ["LD_LIBRARY_PATH"])

        # load model
        self.model = self.load_rknn_model(model_path)

    # Initialize the RKNN model
    def load_rknn_model(self, model_path):
        rknn = RKNNLite()
        print("Loading RKNN model...")

        # Load the RKNN model
        ret = rknn.load_rknn(model_path)
        if ret != 0:
            print("Failed to load RKNN model")
            return None

        # Initialize runtime environment
        ret = rknn.init_runtime()  # Replace with your platform if different
        if ret != 0:
            print("Failed to initialize RKNN runtime")
            return None
        return rknn

    # Run inference using the camera feed
    # Returns list[boxes,confidences,classIds]
    def inferenceFrame(
        self, frame, drawBox = False
    ) -> list[tuple[tuple[int, int], tuple[int, int]], float, int]:
        # Preprocess the frame

        img = utils.letterbox_image(frame.copy())
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = np.expand_dims(img, axis=0)  # Now shape is (1, channels, height, width)
        # Run inference
        predictions = self.model.inference(inputs=[img])
        adjusted = utils.adjustBoxes(predictions[0], frame.shape, ConfigConstants.confThreshold)
        nmsResults = utils.non_max_suppression(adjusted,ConfigConstants.confThreshold)
        # do stuff here
        if drawBox:
            # labels = ["robot", "note"]
            for (bbox, conf, class_id) in nmsResults:
                p1 = tuple(map(int, bbox[:2]))  # Convert to integer tuple
                p2 = tuple(map(int, bbox[2:4]))  # Convert to integer tuple
                cv2.rectangle(frame, p1, p2, (0, 255, 0), 1)  # Drawing the rectangle
                cv2.putText(frame, f"{class_id=} {conf=}", p1, 1, 2, (0, 255, 0), 1)

        return nmsResults


if __name__ == "__main__":
    classes = ["Robot", "Note"]
    inf = rknnInferencer("assets/bestV5.rknn")
    cap = cv2.VideoCapture("assets/video12qual25clipped.mp4")
    cap.set(cv2.CAP_PROP_POS_FRAMES, 1004)
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            startTime = time.time()
            results = inf.inferenceFrame(frame,drawBox=True)
            timePassed = time.time() - startTime
            fps = 1 / timePassed  # seconds
            cv2.putText(frame, f"Fps {fps}", (10, 50), 1, 2, (0, 255, 0), 1)
            cv2.imshow("rknn", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
