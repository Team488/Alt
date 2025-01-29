import time
from Core.Neo import Neo
from Core.Agents.AgentExample import AgentExample

n = Neo()
n.wakeAgent(AgentExample)
n.shutDownOnAgentFinished()
