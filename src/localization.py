from Core.Agents.Abstract.ObjectLocalizingAgentBase import ObjectLocalizingAgentPartial
from Core.Neo import Neo
from tools.Constants import (
    InferenceMode,
    ColorCameraExtrinsics2024,
    CameraIntrinsicsPredefined,
    D435IResolution,
    CommonVideos,
)
from Captures import D435Capture, FileCapture, ConfigurableCameraCapture

agent = ObjectLocalizingAgentPartial(
    D435Capture(D435IResolution.RS480P),
    ColorCameraExtrinsics2024.NONE,
    InferenceMode.ALCOROBEST2025,
    showFrames=True,
)
n = Neo()
n.wakeAgent(agent, isMainThread=True)
