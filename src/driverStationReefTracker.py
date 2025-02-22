from Core.Neo import Neo
from Core.Agents.Abstract import ReefTrackingAgentPartial
from tools.Constants import CameraIntrinsicsPredefined

# removes the temp ip for testing in main
# intr = CameraIntrinsicsPredefined.OAKDLITE1080P
intr = CameraIntrinsicsPredefined.OV9782COLOR

# ReefTracker = ReefTrackingAgentPartial(cameraPath="oakdlite", cameraIntrinsics=intr, showFrames=True)
ReefTracker = ReefTrackingAgentPartial(
    cameraPath=1, cameraIntrinsics=intr, showFrames=True
)

n = Neo()
n.wakeAgent(ReefTracker, isMainThread=True)
n.shutDown()
