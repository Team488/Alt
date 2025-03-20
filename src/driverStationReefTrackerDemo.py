from Core.Neo import Neo
from Core.Agents.Abstract import ReefTrackingAgentPartial
from tools.Constants import (
    CameraIntrinsicsPredefined,
    OAKDLITEResolution,
    D435IResolution,
    CommonVideos,
    SimulationEndpoints,
)
from Captures import ConfigurableCameraCapture, OAKCapture, D435Capture, FileCapture

# intr = CameraIntrinsicsPredefined.OAKDLITE4K
# intr = CameraIntrinsicsPredefined.OV9782COLOR

ReefTracker = ReefTrackingAgentPartial(
    capture=ConfigurableCameraCapture(uniqueId="1",
                                      cameraPath="assets/driverStationVideo.mp4", 
                                      cameraIntrinsics=CameraIntrinsicsPredefined.OAKESTIMATE),
    showFrames=True
)
# ReefTracker = ReefTrackingAgentPartial(cameraPath=0, cameraIntrinsics=intr, showFrames=True)

n = Neo()
n.wakeAgent(ReefTracker, isMainThread=True)
n.shutDown()
n = Neo()