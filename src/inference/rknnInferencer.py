import os
import cv2
import numpy as np
from rknnlite.api import RKNNLite
from inference import utils


class rknnInferencer:
    def __init__(self, model_path, target="rk3588"):
        # export needed rknpu .so
        #so_path = os.getcwd() + "/assets/"

        #os.environ[
        #    "LD_LIBRARY_PATH"
        #] = f"{so_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"

        # Check if LD_LIBRARY_PATH is set correctly
        #print("LD_LIBRARY_PATH:", os.environ["LD_LIBRARY_PATH"])

        # load model
        self.model = self.load_rknn_model(model_path, target)
        self.anchors = utils.loadAnchors("assets/bestV5Anchors.txt")

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
    def getResults(
        self, frame, conf_threshold=0.4
    ) -> list[tuple[tuple[int, int], tuple[int, int]], float, int]:
        # Preprocess the frame
        input_img = utils.letterbox_image(frame)
        input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
        input_img = input_img / 255.0  # Normalize to [0, 1]
        input_img = np.expand_dims(input_img, axis=0).astype(np.float32)

        # Run inference
        outputs = self.model.inference(inputs=[input_img])
        outputs = outputs[0]
        print(outputs.shape)
        if outputs is None:
            print("Error: Inference failed.")
            return None

        adjusted = utils.adjustBoxes(outputs, self.anchors, conf_threshold,printDebug = True)
        nmsResults = utils.non_max_suppression(adjusted,None)

        print(nmsResults)

        return nmsResults
