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
from Core.ShareOperator import ShareOperator


class Agent(ABC):
    DEFAULT_LOOP_TIME = 1 # 1 ms
    def __init__(self, central : Central, xclient : XTablesClient, propertyOperator : PropertyOperator, configOperator : ConfigOperator, shareOperator : ShareOperator, logger : Logger):
        self.central = central
        self.xclient = xclient
        self.propertyOperator = propertyOperator
        self.configOperator = configOperator
        self.shareOp = shareOperator
        self.Sentinel = logger
        # other than setting variables, nothing should go here

    @abstractmethod
    def create(self):        
        """ Runs once when the agent is created"""
        # perform agent init here (eg open camera or whatnot)
        pass

    @abstractmethod
    def runPeriodic(self):
        """ Runs continously until the agent ends"""
        # agent periodic loop here
        pass

    @abstractmethod
    def onClose(self):
        """ Runs once when the agent is finished"""
        # agent cleanup here
        pass

    @abstractmethod
    def isRunning(self) -> bool:
        """ Return a boolean value denoting whether the agent should still be running"""
        # condition to keep agent running here
        pass

    

    # ----- properties -----

    @staticmethod
    @abstractmethod
    def getName():
        """ Please tell me your name"""
        # agent name here
        pass

    @staticmethod
    @abstractmethod
    def getDescription():
        """ Sooo, what do you do for a "living" """
        # agent description here
        pass

    # ----- optional methods -----
    
    def getIntervalMs(self):
        """ how long to wait between each run call """
        # can leave as None, will use default time of 1 ms
        return self.DEFAULT_LOOP_TIME
    
    def forceShutdown(self):
        """ Handle any abrupt shutdown tasks here"""
        # optional code to kill agent immediately here
        pass