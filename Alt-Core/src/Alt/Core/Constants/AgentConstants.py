from abc import abstractmethod
from enum import Enum
from typing import Any, Dict
from functools import partial

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
        agentClass.func.requestProxies()
        return agentClass.func._getProxyRequests()

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
