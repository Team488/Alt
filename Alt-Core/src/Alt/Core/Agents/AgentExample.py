from typing import Any, Optional
from .Agent import Agent


class AgentExample(Agent):
    """ This example agent shows how simple it can be to create a task.
        
        This agent creates a name property (which allows you to change its name), and then it tells it to you 50 times before ending. 
    """
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.nameProp = None
        self.projectNameProp = None
        self.timesRun: int = 0

    def create(self) -> None:
        # for example here i can create a propery to configure what to call myself

        self.nameProp = self.propertyOperator.createProperty(
            propertyTable="agent_name", propertyDefault="Bob"
        )
        self.projectNameProp = self.propertyOperator.createReadOnlyProperty(
            propertyName="agent_name_readonly", propertyValue="bob"
        )
        self.timesRun = 0

    def runPeriodic(self) -> None:
        # task periodic loop here
        # for example, i can tell the world what im called

        self.timesRun += 1
        name = self.nameProp.get()
        self.projectNameProp.set(name)
        self.Sentinel.info(f"My name is {name}")

    def onClose(self) -> None:
        # task cleanup here
        # for example, i can tell the world that my time has come
        if self.nameProp is not None:
            self.Sentinel.info(f"My time has come. Never forget the name {self.nameProp.get()}!")

    def isRunning(self) -> bool:
        # condition to keep task running here
        # for example, i want to run only 50 times. Thus i will be running if the number of times i have run is less than 50
        return self.timesRun < 50

    def forceShutdown(self) -> None:
        # code to kill task immediately here
        # in real code, this is where you could handle things like closing a camera abruptly or anything that would normally be done in the tasks lifespan
        self.Sentinel.info("Shutdown!")

    def getDescription(self) -> str:
        return "Agent_Example_Process"

    def getIntervalMs(self) -> int:
        # how long to wait between each run call
        # for example, i want people to be able to read what i print. So i will wait 1 second
        return 1000
