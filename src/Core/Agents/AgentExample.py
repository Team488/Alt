from abc import ABC, abstractmethod
from abstract.Agent import Agent

class AgentExample(Agent):
    def create(self):        
        # for example here i can create a propery to configure what to call myself
        self.nameProp = self.propertyOperator.createProperty(propertyName="agent_name",propertyDefault="Morpheus")
        self.timesRun = 0
    
    def runPeriodic(self):
        # task periodic loop here
        # for example, i can tell the world what im called
        print(self.nameProp.get())
        print(type(self.nameProp.get()))
        self.timesRun += 1
        pass

    def onClose(self):
        # task cleanup here
        # for example, i can tell the world that my time has come
        print(f"My time has come. Never forget the name {self.nameProp.get()}!")
        pass

    def isRunning(self):
        # condition to keep task running here
        # for example, i want to run only 50 times. Thus i will be running if the number of times i have run is less than 50
        return self.timesRun < 50

    def getIntervalMs(self):
        # how long to wait between each run call
        # for example, i want people to be able to read what i print. So i will wait alot
        return 100 #ms

    def shutdownNow(self):
        # code to kill task immediately here
        # for this example, there are no things to do here
        # in real code, this is where you could handle things like closing a camera abruptly anything that would normally be done in the tasks lifespan
        print("Shutdown!")