from Core.Neo import Neo
from Core.Agents.ReefAndObjectLocalizer import (
    ReefAndObjectLocalizerPartial,
)
from tools.Constants import (
    CameraIntrinsicsPredefined,
    ColorCameraExtrinsics2024,
    InferenceMode,
)


def startDemo() -> None:
    n = Neo()
    frameAgent = ReefAndObjectLocalizerPartial(
        cameraPath="http://localhost:3000/Robot_FrontRight%20Camera?dummy=param.mjpg",
        # cameraPath="assets/reefscapevid.mp4",
        cameraIntrinsics=CameraIntrinsicsPredefined.SIMULATIONCOLOR,
        cameraExtrinsics=ColorCameraExtrinsics2024.FRONTRIGHT,
        inferenceMode=InferenceMode.ONNXSMALL2025,
        showFrames=True,
    )

    n.wakeAgent(frameAgent, isMainThread=True)
    n.waitForAgentsFinished()
