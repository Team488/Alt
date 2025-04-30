import time
from .. import Neo
from ..Agents import Agent
from ..Operators.LogOperator import getChildLogger
from .ensureXTablesServer import ensureXTablesServer

Sentinel = getChildLogger("Agent_Tester")

def test_agent(agentClass : type[Agent]):
    _test_interrupting_running_agent(agentClass)
    _test_getting_agent_info(agentClass)
    _test_running_agent_for_some_time(agentClass)


def _test_interrupting_running_agent(agentClass : type[Agent], numAgents = 4):
    print("---------------Starting _test_interrupting_running_agent_main()---------------")
    ensureXTablesServer()
    n = Neo()

    for _ in range(numAgents):
        n.wakeAgent(agentClass)

    time.sleep(10)

    n.shutDown()

def _test_getting_agent_info(agentClass : type[Agent]):
    print("---------------Starting _test_getting_agent_info()---------------")
    
    agent = agentClass()
    agent.getName()
    agent.getDescription()
    agent.getIntervalMs()

def _test_running_agent_for_some_time(agentClass : type[Agent], n_seconds = 15):
    print("---------------Starting test_running_agent_for_some_time()---------------")
    
    ensureXTablesServer()

    n = Neo()
    
    n.wakeAgent(agentClass, isMainThread=False)
    time.sleep(n_seconds)
    n.shutDown()


