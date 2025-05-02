from Alt.ObjectLocalization.Localization.PipelineStep1 import PipelineStep1
from Alt.ObjectLocalization.Localization.PipelineStep2 import PipelineStep2

from Alt.ObjectLocalization.Inference.ModelConfig import ModelConfig

def test_Step1():
    config = ModelConfig()
    step1 = PipelineStep1()