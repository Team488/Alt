from JXTABLES.TempConnectionManager import TempConnectionManager as tcm
from Core.Agents.BinnedVerticalAlignmentCheck import partialVerticalAlignmentCheck
from Core.Neo import Neo
from Core.Agents import OrangePiAgent

alignment = partialVerticalAlignmentCheck(showFrames=False)
tcm.invalidate()

if __name__ == "__main__":
    n = Neo()
    n.wakeAgent(alignment, isMainThread=False)
    n.wakeAgent(OrangePiAgent, isMainThread=True)
    n.shutDown()
