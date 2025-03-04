from Core.Neo import Neo
from Core.Agents import CalibrationController

n = Neo()
n.wakeAgent(CalibrationController, isMainThread=True)
n.shutDown()
