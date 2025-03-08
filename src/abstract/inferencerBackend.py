from abc import ABC, abstractmethod
from typing import Any, List, Tuple, Callable

import numpy as np
from tools.Constants import YOLOTYPE, InferenceMode
from inference import utils


class InferencerBackend(ABC):
    def __init__(self, mode: InferenceMode) -> None:
        self.mode: InferenceMode = mode
        self.yoloType: YOLOTYPE = self.mode.getYoloType()
        self.labels: List[str] = self.mode.getLabelsAsStr()
        self.adjustBoxes: Callable = utils.getAdjustBoxesMethod(
            self.mode.getYoloType(), self.mode.getBackend()
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
    def postProcess(
        self, results: Any, frame: np.ndarray, minConf: float
    ) -> List[Tuple[List[float], float, int]]:
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
