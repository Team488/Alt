from __future__ import annotations

from abc import abstractmethod
from enum import Enum
from functools import partial
from typing import Any, Dict, cast

from Alt.Core.Agents import Agent


class ProxyType(Enum):

    STREAM = "stream_proxy"
    LOG = "log_proxy"

    @property
    def objectName(self):
        return self.value

    @staticmethod
    def getProxyRequests(agentClass) -> Dict[str, "ProxyType"]:
        if isinstance(agentClass, partial):
            return ProxyType.__getPartialProxyRequests(agentClass)

        return ProxyType.__getAgentProxyRequests(agentClass)

    @staticmethod
    def __getPartialProxyRequests(
        agentClass: partial[type[Agent]],
    ) -> Dict[str, "ProxyType"]:
        agentClassType = cast(Agent, agentClass.func)
        agentClassType.requestProxies()
        return agentClassType._getProxyRequests()

    @staticmethod
    def __getAgentProxyRequests(agentClass: Agent) -> Dict[str, "ProxyType"]:
        agentClass.requestProxies()
        return agentClass._getProxyRequests()


class Proxy:
    @abstractmethod
    def put(self, value: Any):
        pass

    @abstractmethod
    def get(self) -> Any:
        pass
