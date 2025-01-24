from abc import ABC, abstractmethod
class Inferencer(ABC):
    @abstractmethod
    def __init__(self, model_path):
        pass

    @abstractmethod
    def inferenceFrame(self, frame, drawBox=False):
        pass