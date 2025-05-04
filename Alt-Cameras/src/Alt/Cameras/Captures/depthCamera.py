from typing import Tuple, Optional
from abc import abstractmethod

import numpy as np

from .Capture import Capture


class depthCamera(Capture):
    @abstractmethod
    def getDepthAndColorFrame(self) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """Returns a already aligned depth and color frame with a 1-1 pixel mapping"""
        pass

    @abstractmethod
    def getDepthFrame(self) -> Optional[np.ndarray]:
        """Returns only the already aligned depth frame"""
        pass
