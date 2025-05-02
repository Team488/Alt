from Constants.Inference import Object, Backend, YoloType

class ModelConfig:
    def __init__(self, modelPath : str, objects : list[Object], backend : Backend, yoloType : YoloType):
        """ Objects must be in order of class_ids as defined in the model!"""
        self.modelPath = modelPath
        self.objects = objects
        self.backend = backend
        self.yoloType = yoloType

    def getPath(self) -> str:
        return self.modelPath
    
    def getObjects(self) -> list[Object]:
        return self.objects
    
    def getBackend(self) -> Backend:
        return self.backend
    
    def getYoloType(self) -> YoloType:
        return self.YoloType