"""
Multi-Inferencer Module - Unified interface for machine learning inference engines.

This module provides a unified interface to run object detection models across 
different inference backends (RKNN, ONNX, Ultralytics). It abstracts away the
details of model initialization, preprocessing, inference, and postprocessing
to provide a consistent API regardless of the underlying implementation.

The MultiInferencer dynamically loads the appropriate backend based on the
InferenceMode configuration, handles timing/performance tracking, and can
optionally render detection results on input frames.

Features:
- Dynamic backend selection (RKNN, ONNX, Ultralytics/PyTorch)
- Unified preprocessing and postprocessing
- Performance tracking (timing of each inference stage)
- Optional visualization of detection results
"""

import time
from typing import List, Tuple, Optional, Any
import cv2
import numpy as np
from abstract.inferencerBackend import InferencerBackend
from tools.Constants import ConfigConstants, InferenceMode, Backend
from tools import UnitConversion
from Core.LogManager import getLogger
from demos import utils

# Logger instance for the MultiInferencer module
Sentinel = getLogger("Multi_Inferencer")


class MultiInferencer:
    """
    A unified interface for running inference with different inference backends.
    
    This class provides a consistent API for object detection across different 
    backend implementations (RKNN, ONNX, Ultralytics/PyTorch). It handles
    the complete inference pipeline including preprocessing, inference,
    and postprocessing of results.
    
    The MultiInferencer automatically selects and initializes the appropriate
    backend based on the provided InferenceMode. It also tracks performance
    metrics for each stage of inference and can optionally visualize detection
    results on the input frames.
    
    Attributes:
        inferenceMode (InferenceMode): The selected inference mode configuration
        backend (InferencerBackend): The initialized backend implementation
    """
    def __init__(self, inferenceMode: InferenceMode) -> None:
        """
        Initialize the multi-inferencer with a specific inference mode
        
        Args:
            inferenceMode: The inference mode to use (defines model, backend, etc.)
        """
        self.inferenceMode: InferenceMode = inferenceMode
        self.backend: InferencerBackend = self.__getBackend(self.inferenceMode)
        self.backend.initialize()

    def __getBackend(self, inferenceMode: InferenceMode) -> InferencerBackend:
        """
        Get the appropriate backend based on the inference mode
        
        Args:
            inferenceMode: The inference mode to get the backend for
            
        Returns:
            The initialized inferencer backend
            
        Raises:
            RuntimeError: If an invalid backend is specified
        """
        backend = inferenceMode.getBackend()
        if backend == Backend.RKNN:
            from inference.rknnInferencer import rknnInferencer
            return rknnInferencer(mode=inferenceMode)

        if backend == Backend.ONNX:
            from inference.onnxInferencer import onnxInferencer
            return onnxInferencer(mode=inferenceMode)

        if backend == Backend.ULTRALYTICS:
            from inference.ultralyticsInferencer import ultralyticsInferencer
            return ultralyticsInferencer(mode=inferenceMode)

        Sentinel.fatal(f"Invalid backend provided!: {backend}")
        raise RuntimeError(f"Invalid backend provided: {backend}")

    def run(self, frame: np.ndarray, minConf: float, drawBoxes: bool = False) -> Optional[List[Tuple[List[float], float, int]]]:
        """
        Run object detection inference on a frame.
        
        This method performs the complete inference pipeline on the input frame:
        1. Preprocesses the frame into the format required by the model
        2. Runs the actual inference on the preprocessed frame
        3. Postprocesses the model outputs into a usable detection format
        4. Optionally draws detection boxes and performance metrics on the frame
        
        The method also tracks performance metrics for each stage of the pipeline.
        
        Args:
            frame: The input frame to run inference on (BGR format, typically from OpenCV)
            minConf: Minimum confidence threshold for detections (0.0-1.0)
            drawBoxes: Whether to draw bounding boxes on the input frame (modifies frame in-place)
            
        Returns:
            Optional[List[Tuple[List[float], float, int]]]: A list of detections, where each detection
            is a tuple of (bbox, confidence, class_id), or None if inference fails.
            - bbox: List[float] - Bounding box in format [x1, y1, x2, y2] (absolute pixel coordinates)
            - confidence: float - Detection confidence score (0.0-1.0)
            - class_id: int - Class ID index of the detected object
            
        Note:
            If drawBoxes is True, the input frame will be modified in-place to display
            detection boxes and performance metrics.
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
