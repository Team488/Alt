from Core.Neo import Neo
from Core.Agents.Abstract import ReefTrackingAgentPartial
from tools.Constants import CameraIntrinsicsPredefined

# removes the temp ip for testing in main
intr = CameraIntrinsicsPredefined.SIMULATIONCOLOR

ReefTracker = ReefTrackingAgentPartial(cameraPath="oakdlite", cameraIntrinsics=intr, showFrames=True)

n = Neo()
n.wakeAgent(ReefTracker, isMainThread=True)
n.shutDown()
