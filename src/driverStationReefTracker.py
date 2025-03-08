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


ReefTracker = ReefTrackingAgentPartial(
    capture=ConfigurableCameraCapture(
        uniqueId="a",
        cameraPath=CommonVideos.ReefscapeCompilation.path,
        cameraIntrinsics=CameraIntrinsicsPredefined.OV9782COLOR,
    ),
    # capture=OAKCapture(OAKDLITEResolution.OAK1080P),
    showFrames=True,
)
# ReefTracker = ReefTrackingAgentPartial(cameraPath=0, cameraIntrinsics=intr, showFrames=True)
# R

n = Neo()
n.wakeAgent(ReefTracker, isMainThread=True)
n.shutDown()
