# Matrix-Alt-Cameras

**Matrix-Alt-Cameras** is an extension package to the [Matrix-Alt-Core](https://github.com/Team488/Alt/Alt-Core) framework, designed to add camera capabilities to your Alt Agents with minimal setup. This module enables you to easily attach one or more camera streams (e.g., OpenCV, RealSense, OAK-D) to your agents, process frames in real-time, and integrate vision into autonomous systems.

Created by **FRC Team 488** (*Subteam: The Matrix*), this package extends the flexibility of the Alt framework to support robust camera-based tasks like localization, vision tracking, or display overlays.

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

🎯 Features

    🔌 Pluggable Camera Captures: Easily switch between OpenCV, Intel RealSense (D435), Luxonis OAK-D, or even synthetic captures.

    📸 Frame Access: Automatically stores the latest frame as self.latestFrameMain for real-time processing.

    🧠 Agent Integration: Full integration with the Alt Agent model; camera agents can run in parallel and interact with other agents.

    🔍 Calibration Utilities: Built-in support for camera intrinsics, extrinsics, and calibration tools.
