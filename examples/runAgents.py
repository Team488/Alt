from Alt.Core.Agents import Agent
from Alt.Cameras.CameraUsingAgent import CameraUsingAgentBase
from Alt.Cameras.Captures.OpenCVCapture import OpenCVCapture


class TestAgent(Agent):
    def create(self):
        pass

    def runPeriodic(self):
        self.Sentinel.info("Test looogog")

    def getIntervalMs(self):
        return 1000

    def isRunning(self):
        return True

    def getDescription(self):
        return "Test"


class CamTest(CameraUsingAgentBase):
    def __init__(self, **kwargs):
        super().__init__(capture=OpenCVCapture("test",0))

    def getDescription(self):
        return "test-read-webcam"


if __name__ == "__main__":
    from Alt.Core import Neo

    n = Neo()
    n.wakeAgent(TestAgent, isMainThread=False)
    n.wakeAgent(TestAgent, isMainThread=False)
    n.wakeAgent(CamTest, isMainThread=True)
    n.shutDown()
