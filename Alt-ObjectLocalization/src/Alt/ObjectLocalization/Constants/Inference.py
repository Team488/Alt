from enum import Enum
from typing import Any
from Alt.Core.Units import Types, Measurements

class YOLOTYPE(Enum):
    V11 = "v11"
    V8 = "v8"
    V5 = "v5"


class Backend(Enum):
    RKNN = "rknn"
    ONNX = "onnx"
    ULTRALYTICS = "ultralytics"


class Label(Enum):
    # name, w,h (cm)
    ROBOT = ("robot", (75, 75))
    NOTE = ("note", (35, 35))
    ALGAE = ("algae", (41, 41))
    CORAL = ("coral", (30, 12))

    @staticmethod
    def getDefaultLengthType():
        return Units.LengthType.CM

    def __str__(self) -> str:
        return self.value[0]

    def getSize(self, lengthType: Units.LengthType):
        return UnitConversion.convertLength(
            self.getSizeCm(), self.getDefaultLengthType(), lengthType
        )

    def getSizeCm(self):
        return self.value[1]


class ModelType(Enum):
    ALCORO = (Label.ALGAE, Label.CORAL, Label.ROBOT)
    CORO = (Label.CORAL, Label.ROBOT)
    NORO = (Label.NOTE, Label.ROBOT)


class InferenceMode(Enum):
    ONNX2024 = (
        "assets/yolov5s_fp32.onnx",
        "yolov5s-onnx-fp32",
        (Label.ROBOT, Label.NOTE),
        2024,
        Backend.ONNX,
        YOLOTYPE.V5,
        ModelType.NORO,
    )
    ONNXSMALL2025 = (
        "assets/yolov11s_fp32.onnx",
        "yolov11s-onnx-small-fp32",
        (Label.ALGAE, Label.CORAL),
        2025,
        Backend.ONNX,
        YOLOTYPE.V11,
        ModelType.CORO,
    )
    ONNXMEDIUM2025 = (
        "assets/yolov11m_fp32.onnx",
        "yolov11m-onnx-medium-fp32",
        (Label.ALGAE, Label.CORAL),
        2025,
        Backend.ONNX,
        YOLOTYPE.V11,
        ModelType.CORO,
    )
    RKNN2024FP32 = (
        "assets/yolov5s_fp32.rknn",
        "yolov5s-rknn-fp32",
        (Label.ROBOT, Label.NOTE),
        2024,
        Backend.RKNN,
        YOLOTYPE.V5,
        ModelType.NORO,
    )
    RKNN2025INT8 = (
        "assets/yolov11s_int8.rknn",
        "yolov11s-rknn-int8",
        (Label.ALGAE, Label.CORAL),
        2025,
        Backend.RKNN,
        YOLOTYPE.V11,
        ModelType.CORO,
    )

    ULTRALYTICSSMALL2025 = (
        "assets/yolov11s_fp32.pt",
        "yolov11s-pytorch-small-fp32",
        (Label.ALGAE, Label.CORAL),
        2025,
        Backend.ULTRALYTICS,
        YOLOTYPE.V11,
        ModelType.CORO,
    )
    ULTRALYTICSMED2025 = (
        "assets/yolov11m_fp32.pt",
        "yolov11s-pytorch-medium-fp32",
        (Label.ALGAE, Label.CORAL),
        2025,
        Backend.ULTRALYTICS,
        YOLOTYPE.V11,
        ModelType.CORO,
    )
    ALCOROULTRALYTICSSMALL2025BAD = (
        "assets/yolov8s_fp32_BADDD.pt",
        "verybad-yolov8s-pytorch-medium-fp32",
        (Label.ALGAE, Label.CORAL, Label.ROBOT),
        2025,
        Backend.ULTRALYTICS,
        YOLOTYPE.V8,
        ModelType.ALCORO,
    )
    ALCOROBEST2025GPUONLY = (
        "assets/yolo11sBestTensorRT.engine",
        "yolov11s-best-tensorrt",
        (Label.ALGAE, Label.CORAL, Label.ROBOT),
        2025,
        Backend.ULTRALYTICS,
        YOLOTYPE.V11,
        ModelType.ALCORO,
    )
    ALCOROBEST2025 = (
        "assets/yolo11sBest_fp32.pt",
        "yolov11s-best-pytorch",
        (Label.ALGAE, Label.CORAL, Label.ROBOT),
        2025,
        Backend.ULTRALYTICS,
        YOLOTYPE.V11,
        ModelType.ALCORO,
    )

    # TORCH todo!

    def getModelPath(self) -> str:
        return self.value[0]

    def getName(self):
        return self.value[1]

    def getLabelsAsStr(self):
        return list(map(str, self.value[2]))

    def getLabels(self):
        return self.value[2]

    def getYear(self):
        return self.value[3]

    def getBackend(self):
        return self.value[4]

    def getYoloType(self):
        return self.value[5]

    def getModelType(self):
        return self.value[6]

    @classmethod
    def getFromName(cls, name: str, default: Any = None):
        for mode in cls:
            if mode.getName() == name:
                return mode
        return default

    @classmethod
    def assertModelType(
        cls, coreInfMode: "InferenceMode", yourInfMode: "InferenceMode"
    ):
        # your model must be a subset of the core model running
        for label in yourInfMode.getLabels():
            if label not in coreInfMode.getLabels():
                return False
        return True


class Object(Enum):
    ALGAE = "a"
    CORAL = "c"
    NOTE = "n"
    ROBOT = "r"

DEFAULTMODELTABLE = "MainProcessInferenceMODE"
DEFAULTINFERENCEMODE = InferenceMode.ALCOROBEST2025
