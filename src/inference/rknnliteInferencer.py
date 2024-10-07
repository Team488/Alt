import os
import cv2
import numpy as np
from rknnlite.api import RKNNLite


class rknnInferencer:
    def __init__(self, model_path, target="rk3588"):
        # export needed rknpu .so
        so_path = os.getcwd() + "/assets/"

        os.environ[
            "LD_LIBRARY_PATH"
        ] = f"{so_path}:{os.environ.get('LD_LIBRARY_PATH', '')}"

        # Check if LD_LIBRARY_PATH is set correctly
        print("LD_LIBRARY_PATH:", os.environ["LD_LIBRARY_PATH"])

        # load model
        self.model = self.load_rknn_model(model_path, target)

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
        ret = rknn.init_runtime(target)  # Replace with your platform if different
        if ret != 0:
            print("Failed to initialize RKNN runtime")
            return None

        print("RKNN model loaded successfully.")
        return rknn

    # Post-processing for YOLOv5 model (customize as needed)
    def post_process(self, outputs, img_shape):
        results = []
        boxes = []
        confidences = []
        class_ids = []
        # Process outputs from the RKNN model (add decoding logic here)
        return results

    # Run inference using the camera feed
    # Returns list[boxes,confidences,classIds]
    def getResults(
        self, frame
    ) -> list[tuple[tuple[int, int], tuple[int, int]], float, int]:
        # Preprocess the frame
        input_img = cv2.resize(frame, (640, 640))
        input_img = cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB)
        input_img = input_img / 255.0  # Normalize to [0, 1]
        input_img = np.expand_dims(input_img, axis=0).astype(np.float32)

        # Run inference
        outputs = self.model.inference(inputs=[input_img])
        if outputs is None:
            print("Error: Inference failed.")
            return None

        return self.post_process(outputs, frame.shape)
