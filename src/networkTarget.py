from Core.Neo import Neo
from Core.Agents import DriveToNetworkTargetAgent
from Core.Orders import TargetUpdatingOrder

n = Neo()

n.wakeAgent(DriveToNetworkTargetAgent, isMainThread=False)
n.addOrderTrigger("target_pose", TargetUpdatingOrder)
n.waitForAgentsFinished()
