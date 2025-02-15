from Core.Neo import Neo
from abstract.InferenceAgent import (
    InferenceAgentPartial
)
from Core.Agents import FrameDisplayer
from Core.Orders import OrderExample
from tools.Constants import InferenceMode

n = Neo()
infAgent = InferenceAgentPartial(
    cameraPath="assets/reefscapevid.mp4",
    inferenceMode=InferenceMode.ONNXSMALL2025,
)

n.wakeAgent(infAgent, isMainThread=False)
n.addOrderTrigger("example",OrderExample)
# n.wakeAgent(FrameDisplayer, isMainThread=True)
n.waitForAgentsFinished()
