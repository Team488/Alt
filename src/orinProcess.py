from Core.Neo import Neo
from Core.Agents.CentralAgent import CentralAgent

# from Core.Agents.alignmentCheck import partialAlignmentCheck

n = Neo()


n.wakeAgent(CentralAgent, isMainThread=False)
# # n.wakeAgent(alignmentCheck, isMainThread=False)

# start pathplanning rpc
from pathplanning.nmc import fastMarchingMethodRPC

fastMarchingMethodRPC.serve()
