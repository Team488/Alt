from JXTABLES.TempConnectionManager import TempConnectionManager as tcm
from Alignment.DocTrAlignmentProvider import DocTrAlignmentProvider
from Core.Agents.Partials.AlignmentProviderAgent import partialAlignmentCheck
from Core.Neo import Neo
from Core.Agents import OrangePiAgent

alignment = partialAlignmentCheck(
    alignmentProvider=DocTrAlignmentProvider(), showFrames=False
)
tcm.invalidate()

if __name__ == "__main__":
    n = Neo()
    n.wakeAgent(alignment, isMainThread=True)
    # n.wakeAgent(OrangePiAgent, isMainThread=True)
    n.shutDown()
