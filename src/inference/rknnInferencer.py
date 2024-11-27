import os
import time
import cv2
import numpy as np
from rknnlite.api import RKNNLite
from inference import copiedutils
from inference import utils
from inference.coco_utils import COCO_test_helper


class rknnInferencer:
    def __init__(self, model_path="assets/bestV5.rknn", target="rk3588"):
        # export needed rknpu .so
        so_path = os.getcwd() + "/assets/"

        os.environ[
            "LD_LIBRARY_PATH"
        ] = f"{so_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"

        # Check if LD_LIBRARY_PATH is set correctly
        print("LD_LIBRARY_PATH:", os.environ["LD_LIBRARY_PATH"])

        # load model
        self.model = self.load_rknn_model(model_path, target)
        # load anchor
        with open("assets/bestV5Anchors.txt", "r") as f:
            values = [float(_v) for _v in f.readline().split(",")]
            self.anchors = np.array(values).reshape(3, -1, 2).tolist()

        self.co_helper = COCO_test_helper(enable_letter_box=True)

    # Initialize the RKNN model
    def load_rknn_model(self, model_path, target):
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
        self, frame, conf_threshold=0.4
    ) -> list[tuple[tuple[int, int], tuple[int, int]], float, int]:
        # Preprocess the frame

        img = utils.letterbox_image(frame.copy())
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = np.expand_dims(img, axis=0)  # Now shape is (1, channels, height, width)
        # Run inference
        outputs = self.model.inference(inputs=[img])
        print(outputs[0].shape)
        # (boxes, classes, scores) = copiedutils.post_process(outputs, self.anchors)
        adjusted = utils.adjustBoxesRknn(
            outputs[0],
            self.anchors,
            frame.shape,
            doBoxAdjustment=False,
            printDebug=False,
        )

        nms = utils.non_max_suppression(adjusted)
        if len(nms) > 0:
            # realBoxes = self.co_helper.get_real_box(boxes)
            return nms


if __name__ == "__main__":
    classes = ["Robot", "Note"]
    inf = rknnInferencer("assets/bestV5.rknn")
    cap = cv2.VideoCapture("assets/video12qual25clipped.mp4")
    cap.set(cv2.CAP_PROP_POS_FRAMES, 1004)
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            startTime = time.time()
            results = inf.getResults(frame)
            timePassed = time.time() - startTime
            fps = 1 / timePassed  # seconds
            cv2.putText(frame, f"Fps {fps}", (10, 50), 1, 2, (0, 255, 0), 1)
            for result in results:
                (box, score, class_id) = result
                cv2.rectangle(
                    frame, map(int, box[:2]), map(int, box[2:]), (0, 255, 0), 1
                )
                cv2.putText(frame, f"Class {classes[class_id]} Conf {score}")

            cv2.imshow("rknn", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
