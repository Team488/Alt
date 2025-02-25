import time
from Core.Neo import Neo
from Core.Agents.Abstract import ReefTrackingAgentPartial
from tools.Constants import CameraIntrinsicsPredefined
from Core.Agents import ReefVisualizer_XTables_Agent
from reefTracking.ReefVisualizer import ReefVisualizerApp

app = ReefVisualizerApp()

# Attempt to build the visualizer
visualizer = app.build()
visualizerAgent = ReefVisualizer_XTables_Agent.ReefVisualizerAgentPartial(visualizer=visualizer)
n = Neo()
n.wakeAgent(visualizerAgent, isMainThread=False)
app.run()

n.shutDown()
