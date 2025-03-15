from Core.Agents.BinnedVerticalAlignmentCheck import partialVerticalAlignmentCheck
from Core.Neo import Neo

alignmentCheckRight = partialVerticalAlignmentCheck(
    showFrames=True,
    flushTimeMS=-1,
    mjpeg_url="http://photonvisionfrontright.local:1181/stream.mjpg",
)

# alignmentCheckRight = partialVerticalAlignmentCheck(
#     showFrames=True,
#     flushTimeMS=-1,
#     mjpeg_url="http://localhost:1183/stream.mjpg",
# )

n = Neo()

n.wakeAgent(alignmentCheckRight, isMainThread=True)
n.shutDown()
