from Core.Neo import Neo
from Core.Agents import AgentExample
if __name__ == "__main__":
    n = Neo()
    n.wakeAgent(AgentExample)
    n.shutDownOnAgentFinished()
    n.waitForAgentFinished()

