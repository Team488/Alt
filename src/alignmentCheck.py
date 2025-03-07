from Core.Agents.VerticalAlignmentCheckNEW import partialVerticalAlignmentCheck
from Core.Neo import Neo

alignmentCheck = partialVerticalAlignmentCheck(showFrames=True)

n = Neo()

n.wakeAgent(alignmentCheck, isMainThread=True)
n.shutDown()
