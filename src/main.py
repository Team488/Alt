from JXTABLES.TempConnectionManager import TempConnectionManager as tcm
from Core.Neo import Neo
from Core.Agents.Abstract.CentralAgentBase import CentralAgentBase
from tools.Constants import CameraIntrinsicsPredefined, ColorCameraExtrinsics2024

# removes the temp ip for testing in main
tcm.invalidate()

reefAgent = ReefTrackingAgentPartial("http://localhost:3000/Robot_FrontRight%20Camera?dummy=param.mjpg",cameraIntrinsics=CameraIntrinsicsPredefined.SIMULATIONCOLOR,showFrames=True)

n = Neo()
n.wakeAgent(reefAgent, isMainThread=True)
n.shutDown()
# from demos import reefPointDemo
# reefPointDemo.startDemo()