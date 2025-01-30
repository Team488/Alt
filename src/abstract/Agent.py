# agents, otherwise known as tasks will be long running "processes"
# lifespan: 1. create 2. run until shutdown/task finished 2.5 possibly shutdown 3. cleanup. 
# For the most part there will be only one agent running for the whole time
# NOTE: agents will get objects passed into them via the init. There are the "shared" objects across the whole process. 
# For objects pertaining only to agent, create them in the create method

from abc import ABC, abstractmethod
from logging import Logger
from JXTABLES.XTablesClient import XTablesClient
from Core.Central import Central
from Core.PropertyOperator import PropertyOperator
from Core.ConfigOperator import ConfigOperator


class Agent(ABC):
    def __init__(self, central : Central, xclient : XTablesClient, propertyOperator : PropertyOperator, configOperator : ConfigOperator, logger : Logger):
        self.central = central
        self.xclient = xclient
        self.propertyOperator = propertyOperator
        self.configOperator = configOperator
        self.Sentinel = logger
        # other than setting variables, nothing should go here

    
    @abstractmethod
    def create(self):        
        # perform agent init here (eg open camera or whatnot)
        pass

    @abstractmethod
    def runPeriodic(self):
        # agent periodic loop here
        pass

    @abstractmethod
    def onClose(self):
        # agent cleanup here
        pass

    @abstractmethod
    def isRunning(self):
        # condition to keep agent running here
        pass

    @abstractmethod
    def shutdownNow(self):
        # code to kill agent immediately here
        pass

    # ----- properties -----

    @abstractmethod
    def getName(self):
        # agent name here
        pass

    @abstractmethod
    def getDescription(self):
        # agent description here
        pass

    # ----- optional values -----
    
    def getIntervalMs(self):
        # how long to wait between each run call
        # can leave as None, will use default time of 1 ms
        return None