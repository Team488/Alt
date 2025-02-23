from Core.Neo import Neo
from Core.Agents.Abstract.InferenceAgent import InferenceAgentPartial
from Core.Agents import FrameDisplayer
from Core.Orders import OrderExample
from tools.Constants import InferenceMode


def startDemo():
    n = Neo()
    infAgent = InferenceAgentPartial(
        cameraPath="assets/reefscapevid.mp4",
        cameraIntrinsics=None,
        inferenceMode=InferenceMode.ONNXSMALL2025,
    )

    n.wakeAgent(infAgent, isMainThread=False)
    n.addOrderTrigger("example", OrderExample)
    # n.wakeAgent(FrameDisplayer, isMainThread=True)
    n.waitForAgentsFinished()
