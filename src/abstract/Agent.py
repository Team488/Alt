# agents, otherwise known as tasks will be long running "processes"
# lifespan: 1. create 2. run until shutdown/task finished 2.5 possibly shutdown 3. cleanup.
# For the most part there will be only one agent running for the whole time
# NOTE: agents will get objects passed into them via the init. There are the "shared" objects across the whole process.
# For objects pertaining only to agent, create them in the create method

from abc import ABC, abstractmethod
from logging import Logger
from JXTABLES.XTablesClient import XTablesClient
from Core.UpdateOperator import UpdateOperator
from Core.Central import Central
from Core.PropertyOperator import PropertyOperator
from Core.ConfigOperator import ConfigOperator
from Core.ShareOperator import ShareOperator
from Core.TimeOperator import Timer
from tools.Constants import TEAM


class Agent(ABC):
    DEFAULT_LOOP_TIME = 0  # 0 ms

    def __init__(self, **kwargs) -> None:
        # nothing should go here
        self.hasShutdown = False
        self.hasClosed = False
        pass

    def inject(
        self,
        central: Central,
        xclient: XTablesClient,
        propertyOperator: PropertyOperator,
        configOperator: ConfigOperator,
        shareOperator: ShareOperator,
        updateOperator: UpdateOperator,
        logger: Logger,
        timer: Timer,
        isMainThread: bool,
    ) -> None:
        """ "Injects" arguments into agent, should not be modified in any classes"""
        self.central = central
        self.xclient = xclient
        self.propertyOperator = propertyOperator
        self.configOperator = configOperator
        self.shareOp = shareOperator
        self.updateOp = updateOperator
        self.Sentinel = logger
        self.timer = timer
        self.isMainThread = isMainThread
        # other than setting variables, nothing should go here

    def getTimer(self):
        """Use only when needed, and only when associated with agent"""
        return self.timer

    def getTeam(self):
        """Fetches team from XTables, dont trust at the start when everything is initializing"""
        team: str = self.xclient.getString("TEAM")
        if team is None:
            return None

        if team.lower() == "blue":
            return TEAM.BLUE
        else:
            return TEAM.RED

    # ----- Required Implementations -----

    @abstractmethod
    def create(self):
        """Runs once when the agent is created"""
        # perform agent init here (eg open camera or whatnot)
        pass

    @abstractmethod
    def runPeriodic(self):
        """Runs continously until the agent ends"""
        # agent periodic loop here
        pass

    @abstractmethod
    def isRunning(self) -> bool:
        """Return a boolean value denoting whether the agent should still be running"""
        # condition to keep agent running here
        pass

    # ----- properties -----

    @abstractmethod
    def getName(self):
        """Please tell me your name"""
        # agent name here
        pass

    @abstractmethod
    def getDescription(self):
        """Sooo, what do you do for a "living" """
        # agent description here
        pass

    # ----- optional methods -----

    def getIntervalMs(self):
        """how long to wait between each run call
        default is 0, eg no waiting
        """
        # can leave as None, will use default time of 1 ms
        return self.DEFAULT_LOOP_TIME

    def forceShutdown(self) -> None:
        """Handle any abrupt shutdown tasks here"""
        # optional code to kill agent immediately here
        pass

    def onClose(self) -> None:
        """Runs once when the agent is finished"""
        # optional agent cleanup here
        pass
