from Core.Agents.BinnedVerticalAlignmentCheck import BinnedVerticalAlignmentChecker
from Core.Neo import Neo

alignmentCheck = BinnedVerticalAlignmentChecker(showFrames=True, flushTimeMS=200)

n = Neo()

n.wakeAgent(alignmentCheck, isMainThread=True)
n.shutDown()
