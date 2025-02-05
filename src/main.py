from JXTABLES.TempConnectionManager import TempConnectionManager as tcm
from Core.Neo import Neo
from Core.Agents import InferenceAgent, DriveToTargetAgent, OrangePiAgent
from Core.Orders import OrderExample

# removes the temp ip for testing in main
tcm.invalidate()

n = Neo()
n.wakeAgent(DriveToTargetAgent)
n.shutDownOnAgentsFinished()
n.waitForAgentsFinished()
