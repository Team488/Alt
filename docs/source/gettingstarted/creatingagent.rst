Creating an Agent
==================

This guide will walk you through creating agents in the Alt framework, from minimal to advanced implementations.

Basic Agent
-------------------

The simplest agent only requires implementing four abstract methods from the base Agent class:

- ``create()``: Called once when the agent starts
- ``runPeriodic()``: Called repeatedly while the agent is running
- ``isRunning()``: Determines if the agent should continue running
- ``getDescription()``: Returns a description of what the agent does

Here's a minimal example:

.. code-block:: python

    from Alt.Core.Agents import Agent

    class SimpleAgent(Agent):
        def create(self):
            # Initialize any resources here
            self.counter = 0

        def runPeriodic(self):
            # Main agent logic goes here
            self.counter += 1
            self.Sentinel.info(f"Counter: {self.counter}")

        def isRunning(self):
            # Return False when you want the agent to stop
            return self.counter < 10

        def getDescription(self):
            return "A simple counting agent"

This agent will count from 0 to 9 and then stop. The ``Sentinel`` logger is one of many objects automatically injected and available for logging. Other injected objects include:

- ``propertyOperator``: For managing configurable and read-only network properties
- ``configOperator``: For managing configuration files and other file related data
- ``updateOperator``: For sending and receiving global updates. Ie updates that are sent to all agents over the network.
- ``timeOperator``: For timing parts of your agent. You can create timers and when used will automatically measure code blocks.
- ``shareOperator``: For sharing data between agents using rpc based communication.
- ``xclient``: For accessing XTables Server.

These objects provide core functionality that agents can use. For details on how to use properties, see the Properties section below.

Agents can access information about themselves through several properties and methods:

- ``agentName``: The name of the agent instance
- ``isMainThread``: Whether the agent is running in the main thread
- ``getTeam()``: Get the agent's team (BLUE or RED) from XTables

Advanced Agent Features
-------------------

Timing Control
-------------------

You can control how frequently your agent runs by overriding ``getIntervalMs()``:

.. code-block:: python

    def getIntervalMs(self):
        # Run every 500 milliseconds
        return 500

If not overridden, the agent will run as fast as possible (0ms interval).

Cleanup and Shutdown
-------------------

For proper cleanup, you can implement:

- ``onClose()``: Called when the agent finishes normally
- ``forceShutdown()``: Called when the agent needs to stop immediately

.. code-block:: python

    def onClose(self):
        # Clean up resources
        self.Sentinel.info("Cleaning up...")

    def forceShutdown(self):
        # Handle immediate shutdown
        self.Sentinel.info("Emergency shutdown!")

Properties
-------------------

Agents can create and manage properties that can be read/written by other components:

.. code-block:: python

    def create(self):
        # Create a configurable property
        self.nameProp = self.propertyOperator.createProperty(
            propertyTable="agent_name",
            propertyDefault="DefaultName"
        )
        
        # Create a read-only property
        self.statusProp = self.propertyOperator.createReadOnlyProperty(
            propertyName="status",
            propertyValue="initialized"
        )

    def runPeriodic(self):
        name = self.nameProp.get()
        self.statusProp.set(f"Running as {name}")

Bindable Agents
-------------------

If your agent needs constructor arguments, implement the ``BindableAgent`` interface:

.. code-block:: python

    from Alt.Core.Agents import Agent, BindableAgent

    class ConfigurableAgent(Agent, BindableAgent):
        @classmethod
        def bind(cls, name: str, max_count: int):
            return cls._getBindedAgent(name=name, max_count=max_count)

        def __init__(self, name: str, max_count: int):
            super().__init__()
            self.name = name
            self.max_count = max_count
            self.counter = 0

        def create(self):
            self.counter = 0
            self.Sentinel.info(f"Starting {self.name}")

        def runPeriodic(self):
            self.counter += 1
            self.Sentinel.info(f"{self.name}: {self.counter}")

        def isRunning(self):
            return self.counter < self.max_count

        def getDescription(self):
            return f"Configurable agent named {self.name}"

To use this agent, you must bind it first:

.. code-block:: python

    # Create a bound agent instance
    agent = ConfigurableAgent.bind(name="Counter", max_count=5)

Proxies
-------

Agents can request proxies for inter-process communication. First, declare what proxies you need:

.. code-block:: python

    from Alt.Core.Constants.AgentConstants import ProxyType

    class StreamAgent(Agent):
        @classmethod
        def requestProxies(cls):
            # Request a stream proxy named "video"
            cls.addProxyRequest("video", ProxyType.STREAM)

        def __init__(self):
            super().__init__()
            self.video_proxy = None

        def create(self):
            # Get the proxy
            self.video_proxy = self.getProxy("video")
            if self.video_proxy:
                self.Sentinel.info("Video stream proxy acquired")

        def runPeriodic(self):
            if self.video_proxy:
                # Use the proxy to send video frames
                self.video_proxy.send_frame(frame_data)

Best Practices
-------------

1. Always call ``super()`` methods before your own agent methods. 
This is extremly important when you are extending off other agents that perform their own processing first.
***Python will not enforce this***. You must be aware of it yourself
2. Use the injected ``Sentinel`` logger for debugging. It is plumbed in with other telemetry
3. Clean up resources in ``onClose()``
4. Handle errors gracefully in ``forceShutdown()``
5. Use properties for configuration instead of hard-coded values
6. Any initialization code that needs injected agent objects must be put into create() or later. The __init__() method wont have them at that time
7. Remember that every agent runs in separate process, so be careful with shared resources and state.


:doc:`runningagent`.