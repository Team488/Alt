from Core.Agents.alignmentCheck import partialAlignmentCheck
from Core.Neo import Neo

alignmentCheck = partialAlignmentCheck(showFrames=True)

n = Neo()

n.wakeAgent(alignmentCheck, isMainThread=True)
n.shutDown()
