from Core.Agents.Abstract.InferenceAgent import InferenceAgentPartial
from Core.Neo import Neo
from tools.Constants import InferenceMode, CameraIntrinsicsPredefined

agent = InferenceAgentPartial(
    "oakdlite",
    CameraIntrinsicsPredefined.OAKDLITE1080P,
    InferenceMode.ONNXSMALL2025,
    showFrames=True,
)
n = Neo()
n.wakeAgent(agent, isMainThread=True)
