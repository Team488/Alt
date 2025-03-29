from typing import Any, Optional
from abstract.Agent import Agent


class AgentExample(Agent):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.nameProp = None
        self.projectNameProp = None
        self.timesRun: int = 0

    def create(self) -> None:
        # for example here i can create a propery to configure what to call myself
        if self.propertyOperator is None:
            raise ValueError("PropertyOperator not initialized")

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
        if self.nameProp is None or self.projectNameProp is None:
            return

        if self.Sentinel is None:
            return

        self.timesRun += 1
        name = self.nameProp.get()
        self.projectNameProp.set(name)
        self.Sentinel.info(f"My name is {name}")

    def onClose(self) -> None:
        # task cleanup here
        # for example, i can tell the world that my time has come
        if self.nameProp is not None:
            print(f"My time has come. Never forget the name {self.nameProp.get()}!")

    def isRunning(self) -> bool:
        # condition to keep task running here
        # for example, i want to run only 50 times. Thus i will be running if the number of times i have run is less than 50
        return self.timesRun < 10000

    def forceShutdown(self) -> None:
        # code to kill task immediately here
        # for this example, there are no things to do here
        # in real code, this is where you could handle things like closing a camera abruptly anything that would normally be done in the tasks lifespan
        print("Shutdown!")

    def getDescription(self) -> str:
        return "Agent_Example_Process"

    def getIntervalMs(self) -> int:
        # how long to wait between each run call
        # for example, i want people to be able to read what i print. So i will wait alot
        return 1000  # ms
