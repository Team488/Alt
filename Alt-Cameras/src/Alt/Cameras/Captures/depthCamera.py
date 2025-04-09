import numpy as np
from abc import abstractmethod
from typing import Tuple

from .Capture import ConfigurableCapture


class depthCamera(ConfigurableCapture):
    @abstractmethod
    def getDepthAndColorFrame(self) -> Tuple[np.ndarray, np.ndarray]:
        """Returns a already aligned depth and color frame with a 1-1 pixel mapping"""
        pass

    @abstractmethod
    def getDepthFrame(self) -> np.ndarray:
        """Returns only the already aligned depth frame"""
        pass
