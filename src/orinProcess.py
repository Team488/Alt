from Core.Neo import Neo
from Core.Agents.CentralAgent import CentralAgent
from pathplanning.nmc import fastMarchingMethodRPC

n = Neo()

central = n.getCentral()

n.wakeAgent(CentralAgent, isMainThread=False)

# start pathplanning rpc
fastMarchingMethodRPC.serve(central)
