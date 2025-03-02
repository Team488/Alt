from Core.Neo import Neo
from Core.Agents.CentralAgent import CentralAgent
from pathplanning.nmc import fastMarchingMethodRPC

from Core.Agents.alignmentCheck import partialAlignmentCheck

n = Neo()

central = n.getCentral()
alignmentCheck = partialAlignmentCheck(showFrames=False)

n.wakeAgent(CentralAgent, isMainThread=False)
n.wakeAgent(alignmentCheck, isMainThread=False)

# start pathplanning rpc
fastMarchingMethodRPC.serve(central)
