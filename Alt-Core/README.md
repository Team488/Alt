# Matrix-Alt-Core

**Matrix-Alt-Core** is a Matrix-themed Python framework that simplifies defining and running **Agents**. Agents are tasks that you can easily customize by overriding methods, with built-in support for parallel execution, logging, dynamic properties, and more.

Made by **FRC Team 488** (*Subteam: The Matrix*), Matrix-Alt-Core provides the foundational tools for building complex, efficient agent-based systems.

---

## ✨ Features

- **Define Agents**: Create tasks by subclassing the `Agent` class and overriding core methods.
- **Parallel Execution**: Easily run agents concurrently.
- **Automatic Logging**: Built-in logging system for task activity.
- **Dynamic Properties**: Seamlessly define and manage agent attributes.
- **Minimal Boilerplate**: Focus on your task's logic, while the framework handles the infrastructure.

---

## 📦 What’s Inside

Matrix-Alt-Core provides the core infrastructure for:
- Creating and managing Agents.
- Running tasks in parallel or sequentially.
- Tracking agent states and properties automatically.
- Integrating easily into larger systems (e.g., robotics, vision, localization).

---

## 🚀 Getting Started

To get started with Matrix-Alt-Core, install the package via `pip`:

```bash
pip install Matrix-Alt-Core
```

Then create your first agent:

```python
from Alt.Core.Agents import Agent

class AgentExample(Agent):
    """ 
    This example agent shows how simple it can be to create a task.
    
    This agent creates a name property (which allows you to change its name), 
    and then it tells it to you 50 times before ending.
    """
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.nameProp = None
        self.projectNameProp = None
        self.timesRun = 0

    def create(self):
        """ Initialize the agent's properties. """
        self.nameProp = self.propertyOperator.createProperty(
            propertyTable="agent_name", propertyDefault="Bob"
        )
        self.projectNameProp = self.propertyOperator.createReadOnlyProperty(
            propertyName="agent_name_readonly", propertyValue="bob"
        )
        self.timesRun = 0

    def runPeriodic(self):
        """ Periodic task loop. """
        self.timesRun += 1
        name = self.nameProp.get()
        self.projectNameProp.set(name)
        self.Sentinel.info(f"My name is {name}")

    def onClose(self):
        """ Cleanup when the task is closed. """
        if self.nameProp is not None:
            self.Sentinel.info(f"My time has come. Never forget the name {self.nameProp.get()}!")

    def isRunning(self):
        """ Condition to keep the task running. """
        return self.timesRun < 50

    def forceShutdown(self):
        """ Force shutdown the task. """
        self.Sentinel.info("Shutdown!")

    def getDescription(self):
        """ Return the task description. """
        return "Agent_Example_Process"

    def getIntervalMs(self):
        """ Return the time interval between task runs. """
        return 1000  # 1 second

if __name__ == "__main__":
    from Alt.Core import Neo

    n = Neo()
    """ You can run as many agents as you have cpu cores
        Here one agent runs in the background, and another runs on the main thread
    """

    n.wakeAgent(AgentExample, isMainThread=False)
    n.wakeAgent(AgentExample, isMainThread=True)
    n.shutDown()
```

🛠 Project Origins

Matrix-Alt-Core was developed by FRC Team 488, (Subteam: The Matrix). The framework is designed for use in robotics and other complex systems, where tasks (or agents) need to be defined, executed, and managed efficiently in a multi-threaded or parallel environment.

This project is licensed under the MIT License.