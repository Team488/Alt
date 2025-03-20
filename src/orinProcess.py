from Core.Neo import Neo
from Core.Agents.CentralAgent import CentralAgent

from Core.Agents.PathToNearestCoralStation import PathToNearestCoralStation

n = Neo()

central = n.getCentral()

n.wakeAgent(CentralAgent, isMainThread=False)
n.wakeAgent(PathToNearestCoralStation, isMainThread=False)

# start pathplanning rpc
from pathplanning.nmc import fastMarchingMethodRPC

fastMarchingMethodRPC.serve()
