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
if __name__ == "__main__":
    agent = ObjectLocalizingAgentPartial(
        # D435Capture(D435IResolution.RS480P,RealSenseSerialIDS.FRONTLEFTDEPTHSERIALID.value),
        ConfigurableCameraCapture(uniqueId="aa",cameraPath=CommonVideos.Comp2024Clip.path,cameraIntrinsics=CameraIntrinsicsPredefined.OV9782COLOR),
        ColorCameraExtrinsics2024.NONE,
        InferenceMode.ONNXSMALL2025,
        showFrames=True,
    )
    n = Neo()
    n.wakeAgent(agent, isMainThread=False)
    n.waitForAgentsFinished()
