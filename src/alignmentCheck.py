from Core.Agents.BinnedVerticalAlignmentCheck import partialVerticalAlignmentCheck
from Core.Neo import Neo
from tools.Constants import SimulationEndpoints

alignmentCheck = partialVerticalAlignmentCheck(
    showFrames=True,
    flushTimeMS=-1,
    mjpeg_url="http://localhost:1183/stream.mjpg",
)

n = Neo()

n.wakeAgent(alignmentCheck, isMainThread=True)
n.shutDown()
