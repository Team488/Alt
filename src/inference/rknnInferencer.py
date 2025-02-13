import os
import time
import cv2
import numpy as np
from rknnlite.api import RKNNLite
from inference import utils, yolo11RknnUtils
from abstract.inferencerBackend import InferencerBackend
from tools.Constants import ConfigConstants, InferenceMode, YOLOTYPE
from Core.LogManager import getLogger

Sentinel = getLogger("rknn_inferencer")


class rknnInferencer(InferencerBackend):
    def initialize(self):
        # # export needed rknpu .so
        # so_path = os.getcwd() + "/assets/"

        # os.environ[
        #     "LD_LIBRARY_PATH"
        # ] = f"{so_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"

        # # Check if LD_LIBRARY_PATH is set correctly
        # print("LD_LIBRARY_PATH:", os.environ["LD_LIBRARY_PATH"])

        # load model
        self.model = self.load_rknn_model(self.mode.getModelPath())

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

    def preprocessFrame(self, frame):
        # Preprocess the frame by letterboxing, then changing to rgb format and NHWC layout
        img = utils.letterbox_image(frame.copy())
        img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        img = np.expand_dims(
            img, axis=0
        )  # Now shape is NHWC (Batch Size, height, width, channels)
        return [img]  # return as list of input tensors for rknn (one in this case)

    # Returns list[boxes,confidences,classIds]
    def runInference(self, inputTensor):
        return self.model.inference(inputs=inputTensor)

    def postProcess(self, results, frame, minConf):
        if self.mode.getYoloType() == YOLOTYPE.V5:
            adjusted = self.adjustBoxes(results[0], frame.shape, minConf)
            nmsResults = utils.non_max_suppression(adjusted, conf_threshold=minConf)
            return nmsResults
        else:
            boxes, classes, scores = yolo11RknnUtils.post_process(results)
            if boxes is not None:
                return list(zip(boxes,classes,scores))
            return []



if __name__ == "__main__":
    classes = ["Robot", "Note"]
    inf = rknnInferencer("assets/bestV5.rknn")
    cap = cv2.VideoCapture("assets/video12qual25clipped.mp4")
    cap.set(cv2.CAP_PROP_POS_FRAMES, 1004)
    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            startTime = time.time()
            results = inf.inferenceFrame(frame, drawBox=True)
            timePassed = time.time() - startTime
            fps = 1 / timePassed  # seconds
            cv2.putText(frame, f"Fps {fps}", (10, 50), 1, 2, (0, 255, 0), 1)
            cv2.imshow("rknn", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
