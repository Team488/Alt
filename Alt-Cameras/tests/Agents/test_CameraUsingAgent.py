from Alt.Core.TestUtils import AgentTests
from Alt.Cameras.Agents import CameraUsingAgentBase
from Alt.Cameras.Captures import FakeCamera, FakeDepthCamera




def test_regular_capture():
    class CamTest(CameraUsingAgentBase):
        def __init__(self, **kwargs):
            super().__init__(capture=FakeCamera())
            
        def getDescription(self):
            return "Camera test"
        
        def runPeriodic(self):
            super().runPeriodic()
            self.Sentinel.info("LOGLOGLOGLOGLOGLOG")
    
    AgentTests.test_agent(CamTest)


def test_depth_capture():
    class CamTest(CameraUsingAgentBase):
        def __init__(self, **kwargs):
            super().__init__(capture=FakeDepthCamera())
            
        def getDescription(self):
            return "Camera test depth"
    
    AgentTests.test_agent(CamTest)