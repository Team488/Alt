from Core.Agents.Abstract.ObjectLocalizingAgentBase import ObjectLocalizingAgentPartial
from Core.Neo import Neo
from tools.Constants import (
    InferenceMode,
    CameraIntrinsicsPredefined,
    ColorCameraExtrinsics2024,
)

agent = ObjectLocalizingAgentPartial(
    "assets/reefscapevid.mp4",
    CameraIntrinsicsPredefined.OV9782COLOR,
    ColorCameraExtrinsics2024.FRONTRIGHT,
    InferenceMode.ALCOROULTRALYTICSSMALL2025BAD,
    showFrames=True,
)
n = Neo()
n.wakeAgent(agent, isMainThread=True)
