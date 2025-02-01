from Core.Neo import Neo
from Core.Agents import OrangePiAgent
if __name__ == "__main__":
    n = Neo()
    n.wakeAgent(OrangePiAgent)
    n.shutDownOnAgentFinished()
    n.waitForAgentFinished()

