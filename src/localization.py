from Core.Agents.Partials.ObjectLocalizingAgentBase import ObjectLocalizingAgentPartial
from Core.Neo import Neo
from tools.Constants import (
    InferenceMode,
    ColorCameraExtrinsics2024,
    CameraIntrinsicsPredefined,
    D435IResolution,
    RealSenseSerialIDS,
    CommonVideos,
)
from Captures import D435Capture, FileCapture, ConfigurableCameraCapture

agent = ObjectLocalizingAgentPartial(
    D435Capture(D435IResolution.RS480P,RealSenseSerialIDS.FRONTLEFTDEPTHSERIALID.value),
    ColorCameraExtrinsics2024.NONE,
    InferenceMode.ONNXMEDIUM2025,
    showFrames=True,
)
n = Neo()
n.wakeAgent(agent, isMainThread=True)
