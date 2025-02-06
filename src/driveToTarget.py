from Core.Neo import Neo
from Core.Agents import DriveToTargetAgent

if __name__ == "__main__":
    n = Neo()
    n.wakeAgentMain(DriveToTargetAgent)
    n.shutDown()
