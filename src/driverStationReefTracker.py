from Core.Neo import Neo
from Core.Agents.Abstract import ReefTrackingAgentPartial
from tools.Constants import CameraIntrinsicsPredefined

# removes the temp ip for testing in main
intr = CameraIntrinsicsPredefined.OAKDLITE4K
# intr = CameraIntrinsicsPredefined.OV9782COLOR

ReefTracker = ReefTrackingAgentPartial(
    cameraPath="oakdlite", cameraIntrinsics=intr, showFrames=True
)
# ReefTracker = ReefTrackingAgentPartial(cameraPath=0, cameraIntrinsics=intr, showFrames=True)
# R

n = Neo()
n.wakeAgent(ReefTracker, isMainThread=True)
n.shutDown()
