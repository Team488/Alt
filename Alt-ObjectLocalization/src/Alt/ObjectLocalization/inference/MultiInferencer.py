import time
from typing import List, Optional

import cv2
import numpy as np
from Alt.Core import getChildLogger

from .inferencerBackend import InferencerBackend
from ..Constants.Inference import Backend
from .ModelConfig import ModelConfig
from ..Detections.DetectionResult import DetectionResult
from . import utils

Sentinel = getChildLogger("Multi_Inferencer")


class MultiInferencer:
    """
    A unified interface for running inference with different backends (RKNN, ONNX, Ultralytics)
    """

    def __init__(self, modelConfig: ModelConfig) -> None:
        """
        Initialize the multi-inferencer with a specific inference mode

        Args:
            inferenceMode: The inference mode to use (defines model, backend, etc.)
        """
        self.modelConfig = modelConfig
        self.backend = self.__getBackend(self.modelConfig)
        self.backend.initialize()

    def __getBackend(self, modelConfig: ModelConfig) -> InferencerBackend:
        """
        Get the appropriate backend based on the inference mode

        Args:
            inferenceMode: The inference mode to get the backend for

        Returns:
            The initialized inferencer backend

        Raises:
            RuntimeError: If an invalid backend is specified
        """
        backend = modelConfig.getBackend()
        if backend == Backend.RKNN:
            from .backends.rknnInferencer import rknnInferencer

            return rknnInferencer(modelConfig)

        if backend == Backend.ONNX:
            from .backends.onnxInferencer import onnxInferencer

            return onnxInferencer(modelConfig)

        if backend == Backend.ULTRALYTICS:
            from .backends.ultralyticsInferencer import ultralyticsInferencer

            return ultralyticsInferencer(modelConfig)
        
        if backend == Backend.TENSORRT:
            from .backends.TensorrtInferencer import TensorrtInferencer

            return TensorrtInferencer(modelConfig)


        Sentinel.fatal(f"Invalid backend provided!: {backend}")
        raise RuntimeError(f"Invalid backend provided: {backend}")

    def run(
        self, frame: np.ndarray, minConf: float, drawBoxes: bool = False
    ) -> Optional[List[DetectionResult]]:
        """
        Run inference on a frame

        Args:
            frame: The input frame to run inference on
            minConf: Minimum confidence threshold for detections
            drawBoxes: Whether to draw bounding boxes on the frame

        Returns:
            A list of tuples containing (bbox, confidence, class_id) or None if inference fails
        """
        start = time.time_ns()
        if frame is None:
            Sentinel.fatal("Frame is None!")
            return None

        tensor = self.backend.preprocessFrame(frame)
        pre = time.time_ns()
        if tensor is None:
            Sentinel.fatal("Inference Backend preprocessFrame() returned none!")
            return None

        prens = pre - start

        results = self.backend.runInference(inputTensor=tensor)
        inf = time.time_ns()
        if results is None:
            Sentinel.fatal("Inference Backend runInference() returned none!")
            return None

        infns = inf - pre

        processed = self.backend.postProcessBoxes(results, frame, minConf)
        post = time.time_ns()
        if processed is None:
            Sentinel.fatal("Inference Backend postProcess() returned none!")
            return None

        postns = post - inf

        totalTimeElapsedNs = prens + infns + postns
        # Sentinel.debug(f"{totalTimeElapsedNs=} {prens=} {infns=} {postns}")
        cumulativeFps = 1e9 / totalTimeElapsedNs

        # Draw detection boxes and performance metrics if requested
        if drawBoxes:
            cv2.putText(
                frame, f"FPS: {cumulativeFps:.1f}", (10, 20), 1, 1, (255, 255, 255), 1
            )

            for (bbox, conf, class_id) in processed:
                # Get the label for this detection
                label = f"Id out of range!: {class_id}"
                if len(self.backend.labels) > class_id:
                    label = self.backend.labels[class_id]

                utils.drawBox(frame, bbox, label, conf)

        return processed
