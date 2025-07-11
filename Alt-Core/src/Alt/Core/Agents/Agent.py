from __future__ import annotations

from abc import ABC, abstractmethod
from logging import Logger
from typing import Any, Dict, Optional, Protocol, TypeVar, TYPE_CHECKING

from JXTABLES.XTablesClient import XTablesClient

from ..Utils.network import DEVICEIP

if TYPE_CHECKING:
    from ..Constants.AgentConstants import Proxy, ProxyType
    from ..Constants.Teams import TEAM
    from ..Operators.ConfigOperator import ConfigOperator
    from ..Operators.LogStreamOperator import LogStreamOperator
    from ..Operators.PropertyOperator import PropertyOperator
    from ..Operators.ShareOperator import ShareOperator
    from ..Operators.StreamOperator import StreamProxy
    from ..Operators.TimeOperator import TimeOperator, Timer
    from ..Operators.UpdateOperator import UpdateOperator


class Agent(Protocol):
    hasShutdown: bool = False
    hasClosed: bool = False
    isCleanedUp: bool = False
    isMainThread: bool = False
    agentName: str = ""
    xclient: XTablesClient
    propertyOperator: PropertyOperator
    configOperator: ConfigOperator
    updateOp: UpdateOperator
    timeOp: TimeOperator
    Sentinel: Logger
    timer: Timer

    def _injectCore(
        self, shareOperator: ShareOperator, isMainThread: bool, agentName: str
    ) -> None:
        ...

    def _injectNEW(
        self,
        xclient: XTablesClient,  # new
        propertyOperator: PropertyOperator,  # new
        configOperator: ConfigOperator,  # new
        updateOperator: UpdateOperator,  # new
        timeOperator: TimeOperator,  # new
        logger: Logger,  # static/new
    ) -> None:
        ...

    def getProxy(self, proxyName: str) -> Optional[Proxy]:
        ...

    def _setProxies(self, proxies) -> None:
        ...

    def _cleanup(self) -> None:
        ...

    def getTimer(self) -> Timer:
        ...

    def getTeam(self) -> Optional[TEAM]:
        ...

    def _runOwnCreate(self):
        ...

    @classmethod
    def getName(cls) -> str:
        ...

    def create(self) -> None:
        ...

    def runPeriodic(self) -> None:
        ...

    def isRunning(self) -> bool:
        ...

    def getDescription(self) -> str:
        ...

    def getIntervalMs(self) -> int:
        ...

    def forceShutdown(self) -> None:
        ...

    def onClose(self) -> None:
        ...

    @classmethod
    def requestProxies(cls) -> None:
        ...

    @classmethod
    def addProxyRequest(cls, proxyName: str, proxyType: ProxyType) -> None:
        ...

    @classmethod
    def _getProxyRequests(cls) -> Dict[str, ProxyType]:
        ...


TAgent = TypeVar("TAgent", bound=Agent)


class AgentBase(ABC):
    """
    Base class for all agents.
    """

    _proxyRequests: Dict[str, ProxyType] = {}
    DEFAULT_LOOP_TIME: int = 0  # 0 ms
    TIMERS = "timers"

    def __init__(self, **kwargs: Any) -> None:
        # nothing should go here
        self.hasShutdown: bool = False
        self.hasClosed: bool = False
        self.isCleanedUp: bool = False
        self.isMainThread: bool = False
        self.agentName = ""
        self.__proxies: Dict[str, Proxy] = {}

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
        self.timer = self.timeOp.getTimer(self.TIMERS)
        # other than setting variables, nothing should go here

    def _setProxies(self, proxies) -> None:
        self.__proxies = proxies

    def _updateNetworkProxyInfo(self):
        """Put information about the proxies used on xtables. This can be used for the dashboard, and other things"""
        streamPaths = []
        for proxyName, proxy in self.__proxies.items():
            if isinstance(proxy, StreamProxy):
                streamPaths.append(f"{proxyName}|{proxy.getStreamPath()}")

        self.propertyOperator.createCustomReadOnlyProperty(
            "streamPaths", streamPaths, addBasePrefix=True, addOperatorPrefix=True
        )

    def getProxy(self, proxyName: str) -> Optional[Proxy]:
        return self.__proxies.get(proxyName)

    def _cleanup(self) -> None:
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

    def _runOwnCreate(self):
        """The agent wants to do its own stuff too... okay."""

        logIp = f"http://{DEVICEIP}:5000/{self.agentName}/{LogStreamOperator.LOGPATH}"

        self.propertyOperator.createCustomReadOnlyProperty(
            "logIP", logIp, addBasePrefix=True, addOperatorPrefix=True
        )

        self.__ensureProxies()
        self._updateNetworkProxyInfo()

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

    # ----- proxy methods -----
    def __ensureProxies(self) -> None:
        for proxyName, proxyType in self._getProxyRequests().items():
            if (
                proxyName not in self.__proxies
                or type(self.__proxies[proxyName]) is not proxyType
            ):
                print(type(self.__proxies[proxyName]) is proxyType)
                raise RuntimeError(
                    f"Agent proxies are not correcty initialized!\n{self._getProxyRequests()=}\n{self.__proxies.items()=}"
                )

    @classmethod
    def requestProxies(cls):
        """Override this, and add all of your proxy requests"""
        pass

    @classmethod
    def addProxyRequest(cls, proxyName: str, proxyType: ProxyType) -> None:
        """Method to request that a stream proxy will be given to this agent to display streams
        NOTE: you must override requestProxies() and add your calls to this there, or else it will not be used!
        """
        cls._proxyRequests[proxyName] = proxyType

    @classmethod
    def _getProxyRequests(cls) -> Dict[str, ProxyType]:
        return getattr(cls, "_proxyRequests", {})
