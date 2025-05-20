from abc import ABC, abstractmethod
from typing import Any, List, Callable

import numpy as np

from ..Detections.DetectionResult import DetectionResult
from .ModelConfig import ModelConfig
from .backends import utils


class InferencerBackend(ABC):
    def __init__(self, modelConfig: ModelConfig) -> None:
        self.modelConfig = modelConfig
        self.objects = modelConfig.getObjects()
        self.adjustBoxes: Callable = utils.getAdjustBoxesMethod(
            self.modelConfig.getYoloType(), self.modelConfig.getBackend()
        )

    @abstractmethod
    def initialize(self) -> None:
        """Initialize runtime backend here"""
        pass

    @abstractmethod
    def runInference(self, inputTensor: Any) -> Any:
        """Actual model run should be here  \n
        preprocessFrame() will be called before\n
        ------------- runInference() -------------  \n
        postProcess() will be called after  \n
        """
        pass

    @abstractmethod
    def postProcessBoxes(
        self, results: Any, frame: np.ndarray, minConf: float
    ) -> List[DetectionResult]:
        """Place postprocess here.\n
        Should take in raw model output, and return a list of list[boxes,confidences,classIds]
        """
        pass

    @abstractmethod
    def preprocessFrame(self, frame: np.ndarray) -> np.ndarray:
        """Put model preprocess into this method.\n
        What is returned should be a tensorlike object that can immediately be run through the backend
        """
        pass
