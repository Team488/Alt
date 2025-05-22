Running Agents
===================

This guide explains how to run agents using the Matrix-Alt-Core framework, including agent lifecycle, types, and execution modes.

Agent Lifecycle
-------------------

When an agent is started, its methods are called in the following order:

1. ``__init__()`` - Constructor
2. Internal injection of objects, and other initialization
3. ``create()`` - One-time initialization
4. ``isRunning()`` - Checked before each runPeriodic() call
5. ``runPeriodic()`` - Called repeatedly while agent is running
6. ``forceShutdown()`` - Called ONLY if agent is stopped abruptly
7. ``onClose()`` - Called when agent finishes normally
8. Internal Final cleanup

Agent Types
-------------------

There are two main types of agents:

1. **Basic Agents**
   - Inherit directly from ``Agent``
   - Can be instantiated directly

2. **Bindable Agents**
   - Inherit from ``Agent`` and ``BindableAgent``
   - Require arguments in constructor
   - Must be bound before running using the ``bind()`` method
   - Useful for agents that need input arguments

Running Agents
-------------------

Agents can be run in two modes:

1. **Main Thread Mode**
   - Blocks the main thread
   - Good for primary agent or testing. Especially for gui displaying agents.
   - Use ``isMainThread=True``

2. **Background Mode**
   - Runs in separate process
   - Non-blocking
   - Use ``isMainThread=False``

Example Code
-------------------

Here's a complete example showing how to run agents:

.. code-block:: python

    from Alt.Core import Neo
    from Alt.Core.Agents import Agent

    class MyAgent(Agent):
        def create(self):
            self.Sentinel.info("Agent created!")
            
        def runPeriodic(self):
            self.Sentinel.info("Running periodic task")
            
        def isRunning(self):
            return True  # Run forever
            
        def getDescription(self):
            return "My Example Agent"

    if __name__ == "__main__":
        # Create Neo instance
        n = Neo()
        
        # Run agent in background
        n.wakeAgent(MyAgent, isMainThread=False)
        
        # Run another agent in main thread
        n.wakeAgent(MyAgent, isMainThread=True)
        
        # If there were no agents running in main thread, wait for them
        # n.waitForAgentsFinished()
        
        # Clean shutdown to clean resources and ensure all data is saved
        n.shutDown()

Important Notes
-------------------

1. Always use the ``if __name__ == "__main__":`` guard when running agents. It will fail without it. This prevents code from executing multiple times when using multiprocessing.

2. If no agents are running in the main thread, you must call ``waitForAgentsFinished()`` to prevent the program from exiting before agents complete.

3. Always call ``shutDown()`` to ensure proper cleanup of resources and things like properties being saved.

4. For bindable agents, you must bind them before running:

.. code-block:: python

    class ConfigurableAgent(BindableAgent):
        @classmethod
        def bind(cls, config_value):
            return cls._getBindedAgent(config_value)
        def __init__(self, config_value):
            super().__init__()
            self.config = config_value
            
        # ... other required methods ...

    if __name__ == "__main__":
        n = Neo()
        
        # Bind the agent with configuration
        bound_agent = ConfigurableAgent.bind(config_value="test")
        
        # Run the bound agent
        n.wakeAgent(bound_agent) # isMainThread=False by default
        
        n.waitForAgentsFinished()
        n.shutDown()
