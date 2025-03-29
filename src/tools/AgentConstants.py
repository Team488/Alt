from typing import Union, List
from functools import partial
from enum import Enum
from Core.Agents.Abstract import CameraUsingAgentBase
from abstract.Capture import Capture
from abstract.Agent import Agent


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
        # TODO much more here
        capabilites = set()
        for arg in agentClass.args:
            if issubclass(type(arg), Capture):
                capabilites.add(AgentCapabilites.STREAM)

        for arg in agentClass.keywords.values():
            if issubclass(type(arg), Capture):
                capabilites.add(AgentCapabilites.STREAM)

        return list(capabilites)

    @staticmethod
    def __getAgentCapabilites(agentClass: type[Agent]) -> List["AgentCapabilites"]:
        # TODO much more here
        capabilites = set()
        if issubclass(agentClass, CameraUsingAgentBase):
            capabilites.add(AgentCapabilites.STREAM)

        return list(capabilites)
