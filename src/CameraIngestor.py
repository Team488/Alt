from Core.Neo import Neo
from Core.Agents import FrameDisplayer

n = Neo()
n.wakeAgent(FrameDisplayer, isMainThread=True)
n.shutDown()
