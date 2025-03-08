from Core.Agents.BinnedVerticalAlignmentCheck import partialVerticalAlignmentCheck
from Core.Neo import Neo

alignmentCheck = partialVerticalAlignmentCheck(showFrames=True, flushTimeMS=200)

n = Neo()

n.wakeAgent(alignmentCheck, isMainThread=True)
n.shutDown()
