from Core.Agents.BinnedVerticalAlignmentCheck import partialVerticalAlignmentCheck
from Core.Neo import Neo
from tools.Constants import SimulationEndpoints

alignmentCheck = partialVerticalAlignmentCheck(
    showFrames=True,
    flushTimeMS=200,
    mjpeg_url=SimulationEndpoints.FRONTRIGHTAPRILTAGSIM.path,
)

n = Neo()

n.wakeAgent(alignmentCheck, isMainThread=True)
n.shutDown()
