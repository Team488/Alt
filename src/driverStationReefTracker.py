from Core.Neo import Neo
from Core.Agents.Abstract import ReefTrackingAgentPartial
from tools.Constants import (
    CameraIntrinsicsPredefined,
    OAKDLITEResolution,
    D435IResolution,
    CommonVideos,
    SimulationEndpoints,
)
from Captures import ConfigurableCameraCapture, OAKCapture, D435Capture

# removes the temp ip for testing in main
# intr = CameraIntrinsicsPredefined.OAKDLITE4K
# intr = CameraIntrinsicsPredefined.OV9782COLOR

ReefTracker = ReefTrackingAgentPartial(
    capture=D435Capture(D435IResolution.RS480P),
    showFrames=True,
)
# ReefTracker = ReefTrackingAgentPartial(cameraPath=0, cameraIntrinsics=intr, showFrames=True)
# R

n = Neo()
n.wakeAgent(ReefTracker, isMainThread=True)
n.shutDown()
