from JXTABLES.TempConnectionManager import TempConnectionManager as tcm
from Core.Neo import Neo
from Core.Agents import OrangePiAgent
from Core.Agents.VerticalAlignmentCheckNEW import partialVerticalAlignmentCheck

tcm.invalidate()

if __name__ == "__main__":
    n = Neo()
    aligner = partialVerticalAlignmentCheck(showFrames=False)
    n.wakeAgent(aligner, isMainThread=False)
    n.wakeAgent(OrangePiAgent, isMainThread=True)
    n.shutDown()
