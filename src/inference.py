from Core.Agents.Abstract.InferenceAgent import InferenceAgentPartial
from Core.Neo import Neo
from tools.Constants import InferenceMode, CameraIntrinsicsPredefined, CommonVideos
from Captures import FileCapture

agent = InferenceAgentPartial(
    FileCapture(CommonVideos.ReefscapeCompilation.path),
    None,
    InferenceMode.ALCOROULTRALYTICSSMALL2025BAD,
    showFrames=True,
)
n = Neo()
n.wakeAgent(agent, isMainThread=True)
