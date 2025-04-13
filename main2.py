from Alt.Core.Agents import Agent
from Alt.Cameras.Agents import CameraUsingAgent
from Alt.Cameras.Captures.FileCapture import FileCapture

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
    
class CamTest(CameraUsingAgent):
    def __init__(self, **kwargs):
        super().__init__(capture=FileCapture(0))

    def getDescription(self):
        return "test-read-webcam"


if __name__ == "__main__":
    from Alt.Core import Neo
    n = Neo()
    n.wakeAgent(TestAgent, isMainThread=False)
    n.wakeAgent(CamTest, isMainThread=False)
    n.wakeAgent(TestAgent, isMainThread=True)
    n.shutDown()

