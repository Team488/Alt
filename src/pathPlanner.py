from Core.Neo import Neo
from Core.Agents import DriveToTargetAgent

if __name__ == "__main__":
    n = Neo()
    n.wakeAgent(DriveToTargetAgent)
    n.shutDownOnAgentFinished()
    n.waitForAgentFinished()
