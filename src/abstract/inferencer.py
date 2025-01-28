from abc import ABC, abstractmethod
class Inferencer(ABC):
    @abstractmethod
    def __init__(self, model_path):
        # create inferencer here
        pass

    @abstractmethod
    def inferenceFrame(self, frame, drawBox=False):
        # run inference and return results here
        # additionaly draw boxes if asked to
        pass