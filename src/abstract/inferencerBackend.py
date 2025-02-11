from abc import ABC, abstractmethod
from tools.Constants import YOLOTYPE, InferenceMode
from inference.utils import getAdjustBoxesMethod

class InferencerBackend(ABC):
    def __init__(self, mode : InferenceMode):
        self.mode = mode
        self.yoloType = self.mode.getYoloType()
        self.labels = self.mode.getLabels()
        self.adjustBoxes = getAdjustBoxesMethod(self.mode.getYoloType())

    @abstractmethod
    def initialize(self):
        """Initialize runtime backend here"""
        pass

    @abstractmethod
    def runInference(self, inputTensor):
        """ Actual model run should be here  \n
            preprocessFrame() will be called before\n
            ------------- runInference() -------------  \n
            postProcess() will be called after  \n
        """
        pass

    @abstractmethod
    def postProcess(self, results, frame, minConf):
        """ Place postprocess here.\n
            Should take in raw model output, and return a list of list[boxes,confidences,classIds]
        """
        pass
    
    @abstractmethod
    def preprocessFrame(self, frame):
        """ Put model preprocess into this method.\n
            What is returned should be a tensorlike object that can immediately be run through the backend
        """
        pass