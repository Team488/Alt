from Core.Neo import Neo
from Core.Agents import AgentExample
from Core.Orders import OrderExample

from JXTABLES.TempConnectionManager import TempConnectionManager as tcm

# removes the temp ip for testing in main
tcm.invalidate()

n = Neo()
n.wakeAgent(AgentExample)
n.addOrderTrigger("trigger", OrderExample)
n.shutDownOnAgentFinished()
n.waitForAgentFinished()
