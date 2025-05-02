import cv2
import numpy as np

try:
    from rknnlite.api import RKNNLite
except ImportError as e:
    raise RuntimeError(f"The rknn lite package is only supported on arm64!\n{e}")
        
from Alt.Core import getChildLogger

from . import utils, yolo11RknnUtils
from ..inferencerBackend import InferencerBackend
from ...Constants.Inference import YoloType
from ...Detections.DetectionResult import DetectionResult

Sentinel = getChildLogger("rknn_inferencer")


class rknnInferencer(InferencerBackend):
    def initialize(self) -> None:
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

    def postProcessBoxes(self, results, frame, minConf) -> list[DetectionResult]:
        if self.mode.getYoloType() == YoloType.V5:
            adjusted = self.adjustBoxes(results[0], frame.shape, minConf)
            nmsResults = utils.non_max_suppression(adjusted, conf_threshold=minConf)
            return [DetectionResult(nmsResult[0], nmsResult[1], nmsResult[2]) for nmsResult in nmsResults]

        else:
            boxes, classes, scores = yolo11RknnUtils.post_process(results, frame.shape)
            if boxes is not None:
                return [DetectionResult(result[0], result[1], result[2]) for result in zip(boxes, classes, scores)]
            return []

