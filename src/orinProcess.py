from Core.Agents.Abstract import ObjectLocalizingAgentPartial
from Core.Agents.CentralAgent import CentralAgent
from Core.Neo import Neo
from Core.Agents.PathToNearestCoralStation import PathToNearestCoralStation
from tools.Constants import InferenceMode
from Captures import D435Capture

n = Neo()

central = n.getCentral()

n.wakeAgent(CentralAgent, isMainThread=False)
n.wakeAgent(PathToNearestCoralStation, isMainThread=False)

object_localization = ObjectLocalizingAgentPartial(
    inferenceMode=InferenceMode.ALCOROBEST2025GPUONLY, capture=D435Capture()
)

n.wakeAgent(object_localization, isMainThread=False)

# n.wakeAgent(orinIngestorAgent,isMainThread=False)
# n.wakeAgent(
#     partialVideoWriterAgent(FileCapture(0), savePath=f"orinCam_{getTimeStr()}.mp4"),
#     isMainThread=False,
# )

# start pathplanning rpc
from pathplanning.nmc import fastMarchingMethodRPC

fastMarchingMethodRPC.serve()
