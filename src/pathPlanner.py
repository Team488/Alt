from Core.Neo import Neo
from Core.Agents import InteractivePathPlanner

if __name__ == "__main__":
    n = Neo()
    n.wakeAgent(InteractivePathPlanner, isMainThread=True)
    n.waitForAgentsFinished()
    n.shutDown()
