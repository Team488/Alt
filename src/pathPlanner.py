from Core.Neo import Neo
from Core.Agents import DriveToFixedPointAgent, DriveToTargetAgent

if __name__ == "__main__":
    n = Neo()
    # n.wakeAgent(DriveToFixedPointAgent)
    n.wakeAgent(DriveToTargetAgent)
    n.shutDownOnAgentFinished()
    n.waitForAgentFinished()
