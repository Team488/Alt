from Core.Agents.Abstract.InferenceAgent import InferenceAgentPartial
from Core.Neo import Neo
from tools.Constants import InferenceMode, CameraIntrinsicsPredefined, CommonVideos
from Captures import FileCapture, ConfigurableCameraCapture

agent = InferenceAgentPartial(
    ConfigurableCameraCapture(
        "Common_Video",
        CommonVideos.ArucoCalib.path,
        CameraIntrinsicsPredefined.OV9782COLOR,
    ),
    InferenceMode.ALCOROULTRALYTICSSMALL2025BAD,
    showFrames=True,
)
n = Neo()
n.wakeAgent(agent, isMainThread=False)
n.waitForAgentsFinished()
