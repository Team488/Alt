# agents, otherwise known as tasks will be long running "processes"
# lifespan: 1. create 2. run until shutdown/task finished 2.5 possibly shutdown 3. cleanup.
# For the most part there will be only one agent running for the whole time
# NOTE: agents will get objects passed into them via the init. There are the "shared" objects across the whole process.
# For objects pertaining only to agent, create them in the create method

from abc import ABC, abstractmethod
from logging import Logger
import multiprocessing
import multiprocessing.managers
from typing import Optional, Any

from JXTABLES.XTablesClient import XTablesClient
from ..Operators.UpdateOperator import UpdateOperator
from ..Operators.PropertyOperator import PropertyOperator
from ..Operators.ConfigOperator import ConfigOperator
from ..Operators.ShareOperator import ShareOperator
from ..Operators.TimeOperator import TimeOperator, Timer
from ...Constants.Teams import TEAM
from ...Constants.AgentConstants import AgentCapabilites



class Agent(ABC):
    DEFAULT_LOOP_TIME: int = 0  # 0 ms

    def __init__(self, **kwargs: Any) -> None:
        # nothing should go here
        self.hasShutdown: bool = False
        self.hasClosed: bool = False
        self.isCleanedUp: bool = False
        self.xclient: Optional[XTablesClient] = None
        self.propertyOperator: Optional[PropertyOperator] = None
        self.configOperator: Optional[ConfigOperator] = None
        self.shareOp: Optional[ShareOperator] = None
        self.updateOp: Optional[UpdateOperator] = None
        self.Sentinel: Optional[Logger] = None
        self.timer: Optional[Timer] = None
        self.extraObjects = {}
        self.isMainThread: bool = False
        self.agentName = ""

    def _injectCore(
        self, shareOperator: ShareOperator, isMainThread: bool, agentName: str
    ) -> None:
        """
        "Injects" arguments into agent, should not be modified in any classes

        Some things can be passed in from core. The objects are picklable/should be shared
        For example the shareOperator uses a rpc based dict, should only be one.
        """
        self.isMainThread = isMainThread
        self.shareOp = shareOperator
        self.agentName = agentName

    def _injectNEW(
        self,
        xclient: XTablesClient,  # new
        propertyOperator: PropertyOperator,  # new
        configOperator: ConfigOperator,  # new
        updateOperator: UpdateOperator,  # new
        timeOperator: TimeOperator,  # new
        logger: Logger,  # static/new
    ) -> None:
        """
        "Injects" arguments into agent, should not be modified in any classes

        Some things will be instantiated just for this agent, they arent picklable/dont play well with process pools
        """
        self.xclient = xclient
        self.propertyOperator = propertyOperator
        self.configOperator = configOperator
        self.updateOp = updateOperator
        self.timeOp = timeOperator
        self.Sentinel = logger
        self.timer = self.timeOp.getTimer("timers")
        # other than setting variables, nothing should go here

    def _setExtraObjects(self, extraObjects: multiprocessing.managers.DictProxy):
        self.extraObjects = extraObjects

    def _cleanup(self):
        # xclient shutdown occasionally failing?
        # self.xclient.shutdown()
        self.propertyOperator.deregisterAll()
        self.updateOp.deregister()

    def getTimer(self) -> Timer:
        """Use only when needed, and only when associated with agent"""
        if self.timer is None:
            raise ValueError("Timer not initialized")
        return self.timer

    def getTeam(self) -> Optional[TEAM]:
        """Fetches team from XTables, dont trust at the start when everything is initializing"""
        if self.xclient is None:
            raise ValueError("XTablesClient not initialized")

        team: Optional[str] = self.xclient.getString("TEAM")
        if team is None:
            return None

        if team.lower() == "blue":
            return TEAM.BLUE
        else:
            return TEAM.RED

    @classmethod
    def getName(cls):
        return cls.__name__

    # ----- Required Implementations -----

    @abstractmethod
    def create(self) -> None:
        """Runs once when the agent is created"""
        # perform agent init here (eg open camera or whatnot)
        pass

    @abstractmethod
    def runPeriodic(self) -> None:
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
    def getDescription(self) -> str:
        """Sooo, what do you do for a "living" """
        # agent description here
        pass

    # ----- optional methods -----

    def getIntervalMs(self) -> int:
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
    @classmethod
    def getCapabilites(cls) -> list[AgentCapabilites]:
        return [] 

