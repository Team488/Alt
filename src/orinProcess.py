from Core.Neo import Neo
from Core.Agents.CentralAgentBase import CentralAgentBase
from pathplanning.nmc import fastMarchingMethodRPC

n = Neo()

central = n.__central

n.wakeAgent(CentralAgentBase, isMainThread=False)

# start pathplanning rpc
fastMarchingMethodRPC.serve()
