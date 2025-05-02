# Matrix-Alt-Cameras

**Matrix-Alt-Cameras** is an extension package to the [Matrix-Alt-Core](https://pypi.org/project/Matrix-Alt-Core/) framework, designed to add camera capabilities to your Alt Agents with minimal setup. 
---

## 🚀 Quick Start

Here's a basic example using an OpenCV-compatible webcam:

```python
from Alt.Core.Agents import Agent
from Alt.Cameras.CameraUsingAgent import CameraUsingAgentBase
from Alt.Cameras.Captures.OpenCVCapture import OpenCVCapture
import cv2

class CamTest(CameraUsingAgentBase):
    def __init__(self):
        super().__init__(capture=OpenCVCapture("test", 0))

    def runPeriodic(self):
        super().runPeriodic()
        cv2.putText(self.latestFrameMain, "This test will be displayed on top of the frame", (10, 20), 1, 1, (255, 255, 255), 1)

    def getDescription(self):
        return "test-read-webcam"

if __name__ == "__main__":
    from Alt.Core import Neo

    n = Neo()
    n.wakeAgent(CamTest, isMainThread=True)
    n.shutDown()
```
