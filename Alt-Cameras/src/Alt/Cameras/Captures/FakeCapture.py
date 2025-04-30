from abc import ABC, abstractmethod
from typing import Tuple
import numpy as np
from .Capture import Capture
from .depthCamera import depthCamera 


class FakeCamera(Capture):
    def __init__(self, name : str = "fakeCam", fakeFrame : np.ndarray = None):
        super().__init__(name)
        self.fakeFrame = fakeFrame or np.ones((640, 480, 3), dtype=np.uint8) * 255
    
    def create(self) -> None:
        pass

    def getMainFrame(self) -> np.ndarray:
        return self.fakeFrame

    def getFps(self) -> int:
        return 9999999

    def isOpen(self) -> bool:
        return True

    def close(self) -> None:
        pass

class FakeDepthCamera(depthCamera):
    def __init__(self, name : str = "fakeCam", fakeFrame : np.ndarray = None):
        super().__init__(name)
        self.fakeColor = fakeFrame or np.ones((640, 480, 3), dtype=np.uint8) * 255
        self.fakeDepth = fakeFrame or np.ones((640, 480), dtype=np.uint8) * 255

    def create(self) -> None:
        pass

    def getDepthAndColorFrame(self) -> Tuple[np.ndarray, np.ndarray]:
        return (self.fakeDepth, self.fakeColor)

    def getDepthFrame(self) -> np.ndarray:
        return self.fakeDepth

    def getMainFrame(self) -> np.ndarray:
        return self.fakeColor

    def getFps(self) -> int:
        return 999999

    def isOpen(self) -> bool:
        return True

    def close(self) -> None:
        pass