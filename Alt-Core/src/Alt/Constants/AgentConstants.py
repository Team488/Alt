from typing import Union, List
from functools import partial
from enum import Enum
from Alt.Core.Agents import Agent


class AgentCapabilites(Enum):

    STREAM = "stream_queue"

    @property
    def objectName(self):
        return self.value

    @staticmethod
    def getCapabilites(
        agentClass: Union[partial, type[Agent]]
    ) -> List["AgentCapabilites"]:
        if isinstance(agentClass, partial):
            return AgentCapabilites.__getPartialCapabilites(agentClass)

        return AgentCapabilites.__getAgentCapabilites(agentClass)

    @staticmethod
    def __getPartialCapabilites(agentClass: partial) -> List["AgentCapabilites"]:
        return list(set(agentClass.func.getCapabilites()))

    @staticmethod
    def __getAgentCapabilites(agentClass: type[Agent]) -> List["AgentCapabilites"]:
        return list(set(agentClass.getCapabilites()))

