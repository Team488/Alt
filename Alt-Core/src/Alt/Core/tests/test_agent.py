import time
from ..Agents import AgentExample
from ..Neo import Neo
from ...Common.ensureXTablesServer import ensureXTablesServer

def test_interrupting_running_agents():
    ensureXTablesServer()

    n = Neo()
    n.wakeAgent(AgentExample)
    n.wakeAgent(AgentExample)
    n.wakeAgent(AgentExample)
    n.wakeAgent(AgentExample)
    for i in range(10):
        print(f"Test loop #{i}") 
        time.sleep(1)

    n.shutDown()

def test_many_main_agents():
    ensureXTablesServer()


    class superFastAgent(AgentExample):
        def getIntervalMs(self):
            return 1 # make it go very fast

    n = Neo()
    
    n.wakeAgent(superFastAgent, isMainThread=True)
    n.wakeAgent(superFastAgent, isMainThread=True)
    n.wakeAgent(superFastAgent, isMainThread=True)
    n.wakeAgent(superFastAgent, isMainThread=True)
    n.wakeAgent(superFastAgent, isMainThread=True)
    n.wakeAgent(superFastAgent, isMainThread=True)

    n.shutDown()

def test_simple_running_agent_main():
    ensureXTablesServer()


    class superFastAgent(AgentExample):
        def getIntervalMs(self):
            return 1 # make it go very fast

    n = Neo()
    
    n.wakeAgent(superFastAgent, isMainThread=True)
    n.shutDown()

def test_simple_running_agent_async():
    ensureXTablesServer()

    class superFastAgent(AgentExample):
        def getIntervalMs(self):
            return 1 # make it go very fast

    n = Neo()
    
    n.wakeAgent(superFastAgent, isMainThread=False)
    n.waitForAgentsFinished()
    n.shutDown()

