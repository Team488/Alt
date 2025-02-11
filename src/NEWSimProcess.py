from Core.Neo import Neo
from abstract.FrameProcessingAgentBase import (
    PartialFrameProcessingAgent,
    FrameProcessingAgent,
)
from tools.Constants import CameraIntrinsics, CameraExtrinsics, InferenceMode

n = Neo()
frameAgent = PartialFrameProcessingAgent(
    # cameraPath="http://localhost:3000/Robot_FrontRight%20Camera?dummy=param.mjpg",
    cameraPath="assets/reefscapevid.mp4",
    cameraIntrinsics=CameraIntrinsics.SIMULATIONCOLOR,
    cameraExtrinsics=CameraExtrinsics.FRONTRIGHT,
    inferenceMode=InferenceMode.ONNXSMALL2025,
)

n.wakeAgent(frameAgent, isMainThread=True)
n.waitForAgentsFinished()
