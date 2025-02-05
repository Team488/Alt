from JXTABLES.TempConnectionManager import TempConnectionManager as tcm
from Core.Neo import Neo
from Core.Agents import OrangePiAgent

tcm.invalidate()

if __name__ == "__main__":
    n = Neo()
    n.wakeAgent(OrangePiAgent)
    n.shutDownOnAgentsFinished()
    n.waitForAgentsFinished()

