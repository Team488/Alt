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
    ConfigurableCameraCapture(
        CommonVideos.Comp2024Clip.path, CameraIntrinsicsPredefined.OV9782COLOR
    ),
    ColorCameraExtrinsics2024.FRONTRIGHT,
    InferenceMode.ONNX2024,
    showFrames=True,
)
n = Neo()
n.wakeAgent(agent, isMainThread=True)
