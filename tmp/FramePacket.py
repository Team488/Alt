

if __name__ == "__main__":
    from Alt.Cameras.Agents import CameraUsingAgent
    from Alt.Core import Neo
    from Alt.Core.Agents import AgentExample

    n = Neo()

    n.wakeAgent(AgentExample, isMainThread=True)

    n.shutDown()