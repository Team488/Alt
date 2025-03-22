from Core.Neo import Neo
from Core.Agents.PathToNearestCoralStation import PathToNearestCoralStation
from Core.Agents.orinIngestorAgent import orinIngestorAgent
from Core.Agents.orinIngestorAgent import getTimeStr
from Core.Agents.VideoWriterAgent import partialVideoWriterAgent
from Captures import FileCapture

n = Neo()

# central = n.getCentral()
#
# n.wakeAgent(CentralAgent, isMainThread=False)
n.wakeAgent(PathToNearestCoralStation, isMainThread=False)
# n.wakeAgent(orinIngestorAgent,isMainThread=False)
n.wakeAgent(
    partialVideoWriterAgent(FileCapture(0), savePath=f"orinCam_{getTimeStr()}.mp4"),
    isMainThread=False,
)

# start pathplanning rpc
from pathplanning.nmc import fastMarchingMethodRPC

fastMarchingMethodRPC.serve()
