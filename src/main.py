from Core.Neo import Neo
from Core.Agents import AgentExample
from Core.Orders import OrderExample
n = Neo()
n.wakeAgent(AgentExample)
n.addOrderTrigger("trigger",OrderExample)
n.shutDownOnAgentFinished()
n.waitForAgentFinished()