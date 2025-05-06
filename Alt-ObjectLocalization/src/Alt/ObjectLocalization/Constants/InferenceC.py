from enum import Enum

from Alt.Core.Units import Conversions, Types

from ..Localization.DepthEstimationMethod import DepthEstimationMethod


class DefaultConfigConstants:
    confThreshold = 0.7
    drawBoxes = False
    maxDetection = None


class YoloType(Enum):
    V11 = "v11"
    V8 = "v8"
    V5 = "v5"


from enum import Enum

class Backend(Enum):
    ONNX = "onnx"
    ULTRALYTICS = "ultralytics"
    RKNN = "rknn"
    TENSORRT = "tensorrt"

available_backends = set()

try:
    from ..Inference import rknnInferencer
    available_backends.add(Backend.RKNN)
except ImportError:
    pass

try:
    from ..Inference import TensorrtInferencer
    available_backends.add(Backend.TENSORRT)
except ImportError:
    pass

# Always available ones
available_backends.add(Backend.ONNX)
available_backends.add(Backend.ULTRALYTICS)


class Object:
    def __init__(self, name : str, sizeCM : tuple[int, int], depthEstimationMethod : DepthEstimationMethod = None):
        self.name = name
        self.depthMethod = depthEstimationMethod
        self.sizeCM = sizeCM

