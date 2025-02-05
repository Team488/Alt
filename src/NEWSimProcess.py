from Core.Neo import Neo
from abstract.FrameProcessingAgentBase import PartialFrameProcessingAgent, FrameProcessingAgent
from tools.Constants import CameraIntrinsics, CameraExtrinsics, InferenceMode
n = Neo()
frameAgent = PartialFrameProcessingAgent(cameraPath="http://localhost:3000/Robot_FrontRight%20Camera?dummy=param.mjpg",
                                         cameraIntrinsics=CameraIntrinsics.SIMULATIONCOLOR, 
                                         cameraExtrinsics=CameraExtrinsics.FRONTRIGHT,
                                         inferenceMode=InferenceMode.ONNX2024)
n.wakeAgentPartial(frameAgent,FrameProcessingAgent.getName())
n.waitForAgentsFinished()