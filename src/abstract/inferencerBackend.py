"""
InferencerBackend Module - Abstract interface for machine learning inference backends.

This module defines the base interface for all inference backends in the system,
which are components that execute machine learning models for object detection.
Different backends support various hardware acceleration technologies and model formats.

The InferencerBackend abstract class provides a consistent interface for model
initialization, preprocessing, inference execution, and postprocessing across
different backend implementations (ONNX, RKNN, Ultralytics/PyTorch).
"""

from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Callable

import numpy as np
from tools.Constants import YOLOTYPE, InferenceMode
from inference import utils


class InferencerBackend(ABC):
    """
    Abstract base class for all machine learning inference backends.
    
    This class defines the interface that all inference backends must implement,
    providing methods for model initialization, preprocessing, inference execution,
    and postprocessing. It handles the complete inference pipeline for object detection
    models, with specific implementations for different backend technologies.
    
    Attributes:
        mode (InferenceMode): The inference mode configuration
        yoloType (YOLOTYPE): The YOLO model version being used
        labels (List[str]): List of class labels the model can detect
        adjustBoxes (Callable): Function to adjust bounding boxes based on model type
    """
    def __init__(self, mode: InferenceMode) -> None:
        """
        Initialize the inferencer backend with the specified inference mode.
        
        Args:
            mode: The inference mode configuration that specifies the model,
                 backend type, and other parameters
        """
        self.mode: InferenceMode = mode
        self.yoloType: YOLOTYPE = self.mode.getYoloType()
        self.labels: List[str] = self.mode.getLabelsAsStr()
        self.adjustBoxes: Callable = utils.getAdjustBoxesMethod(
            self.mode.getYoloType(), self.mode.getBackend()
        )

    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the inference runtime backend.
        
        This method should perform all necessary initialization for the backend,
        such as loading model weights, creating runtime sessions, and allocating
        resources. It is called once before any inference operations.
        
        Raises:
            Exception: If the backend cannot be initialized
        """
        pass

    @abstractmethod
    def runInference(self, inputTensor: Any) -> Any:
        """
        Execute inference on the preprocessed input tensor.
        
        This method runs the actual model inference on the preprocessed input.
        It is the middle step in the inference pipeline:
        preprocessFrame() -> runInference() -> postProcessBoxes()
        
        Args:
            inputTensor: The preprocessed input tensor in the format expected by the model
            
        Returns:
            Any: The raw model outputs, which will be passed to postProcessBoxes()
            
        Raises:
            Exception: If inference fails
        """
        pass

    @abstractmethod
    def postProcessBoxes(
        self, results: Any, frame: np.ndarray, minConf: float
    ) -> List[Tuple[List[float], float, int]]:
        """
        Process raw model outputs into detection results.
        
        This method converts the raw model outputs into a standardized format
        of bounding boxes, confidence scores, and class IDs. It applies
        confidence thresholding to filter low-confidence detections.
        
        Args:
            results: The raw model outputs from runInference()
            frame: The original input frame (for reference dimensions)
            minConf: Minimum confidence threshold for detections
            
        Returns:
            List[Tuple[List[float], float, int]]: A list of detections, where each detection
                is a tuple of (bbox, confidence, class_id)
                - bbox: List[float] - Bounding box in format [x1, y1, x2, y2]
                - confidence: float - Detection confidence score
                - class_id: int - Class ID index
        """
        pass

    @abstractmethod
    def preprocessFrame(self, frame: np.ndarray) -> np.ndarray:
        """
        Preprocess a frame for inference.
        
        This method transforms the input frame into the format expected by the model,
        which may include resizing, normalization, channel reordering, and other
        preprocessing steps specific to the model.
        
        Args:
            frame: The input frame to preprocess (typically BGR format from OpenCV)
            
        Returns:
            np.ndarray: The preprocessed tensor ready for inference
        """
        pass
