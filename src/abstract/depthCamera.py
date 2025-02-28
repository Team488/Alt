import numpy as np
from abc import abstractmethod
from abstract.Capture import ConfigurableCapture


class depthCamera(ConfigurableCapture):
    @abstractmethod
    def getDepthAndColorFrame(self) -> tuple[np.ndarray]:
        """Returns a already aligned depth and color frame with a 1-1 pixel mapping"""
        pass

    @abstractmethod
    def getDepthFrame(self):
        """Returns only the already aligned depth frame"""
        pass
