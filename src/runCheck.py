from Core.Agents.AlignmentCheck import partialAlignmentCheck
from Core.Neo import Neo

checker = partialAlignmentCheck(showFrames=True)
n = Neo()

n.wakeAgent(checker, isMainThread=True)
n.shutDown()
