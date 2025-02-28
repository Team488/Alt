from Core.Agents.Abstract.InferenceAgent import InferenceAgentPartial
from Core.Neo import Neo
from tools.Constants import InferenceMode, CameraIntrinsicsPredefined

agent = InferenceAgentPartial(
    "assets/reefscapevid.mp4",
    None,
    InferenceMode.ALCOROULTRALYTICSSMALL2025BAD,
    showFrames=True,
)
n = Neo()
n.wakeAgent(agent, isMainThread=True)
