import cv2
import time
import numpy as np
import tensorrt as trt
import pycuda.autoinit
import pycuda.driver as cuda

from typing import Any
from inference.utils import getAdjustBoxesMethod
from tools.Constants import InferenceMode
from abstract.inferencerBackend import InferencerBackend

EXPLICIT_BATCH = 1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH)
TRT_LOGGER = trt.Logger(trt.Logger.INFO)


class TensorrtInferencer(InferencerBackend):
    def __init__(self, mode: InferenceMode) -> None:
        super().__init__(mode)
        self.engine_path = mode.getModelPath()
        self.engine = None
        self.context = None
        self.stream = None
        self.bindings = []
        self.host_inputs = []
        self.cuda_inputs = []
        self.host_outputs = []
        self.cuda_outputs = []

    def initialize(self) -> None:
        """Loads the TensorRT engine and prepares execution context."""
        with open(self.engine_path, "rb") as f:
            serialized_engine = f.read()

        runtime = trt.Runtime(TRT_LOGGER)
        self.engine = runtime.deserialize_cuda_engine(serialized_engine)
        self.context = self.engine.create_execution_context()
        self.stream = cuda.Stream()

        for binding in self.engine:
            size = trt.volume(self.engine.get_tensor_shape(binding))
            host_mem = cuda.pagelocked_empty(shape=[size], dtype=np.float32)
            cuda_mem = cuda.mem_alloc(host_mem.nbytes)
            self.bindings.append(int(cuda_mem))

            if self.engine.get_tensor_mode(binding) == trt.TensorIOMode.INPUT:
                self.host_inputs.append(host_mem)
                self.cuda_inputs.append(cuda_mem)
            else:
                self.host_outputs.append(host_mem)
                self.cuda_outputs.append(cuda_mem)

    def preprocessFrame(self, frame: np.ndarray) -> np.ndarray:
        """Prepares the input image for inference."""
        frame = (2.0 / 255.0) * frame.transpose((2, 0, 1)) - 1.0
        return frame.astype(np.float32).ravel()

    def runInference(self, inputTensor: np.ndarray) -> Any:
        """Runs inference on the processed input tensor."""
        np.copyto(self.host_inputs[0], inputTensor)

        cuda.memcpy_htod_async(self.cuda_inputs[0], self.host_inputs[0], self.stream)
        self.context.execute_v2(self.bindings)
        cuda.memcpy_dtoh_async(self.host_outputs[0], self.cuda_outputs[0], self.stream)
        self.stream.synchronize()

        return self.host_outputs[0]

    def postProcessBoxes(
        self, results, frame, minConf
    ) -> list[tuple[list[float, float, float, float], float, int]]:
        """Processes raw output from the model to return bounding boxes, confidences, and class IDs."""
        return self.adjustBoxes(results, frame, minConf)
