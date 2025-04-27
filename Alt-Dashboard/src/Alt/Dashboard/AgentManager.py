from Alt.Core.Operators.PropertyOperator import PropertyOperator
from Alt.Core.Operators.ConfigOperator import ConfigOperator
from JXTABLES.XTablesClient import XTablesClient
from Alt.Core.Agents import Agent
from Alt.Core.Operators.AgentOperator import AgentOperator
from Alt.Core.Operators.UpdateOperator import UpdateOperator


class AgentManager:
    def __init__(self):
        self.cachedAgentSubscriptions = {}
        self.client = XTablesClient(debug_mode=True)
        self.propertyGenerator = PropertyOperator(XTablesClient(), ConfigOperator())

        self.allRunningAgents = (
            self.propertyGenerator.createReadExistingNetworkValueProperty(
                UpdateOperator.ALLRUNNINGAGENTPATHS,
                self.client.getStringList(UpdateOperator.ALLRUNNINGAGENTPATHS),
            )
        )
        self.currentRunningAgents = (
            self.propertyGenerator.createReadExistingNetworkValueProperty(
                UpdateOperator.CURRENTLYRUNNINGAGENTPATHS,
                self.client.getStringList(UpdateOperator.CURRENTLYRUNNINGAGENTPATHS),
            )
        )

    def getSubscription(self, agentBaseName: str) -> "AgentSubscription":
        if agentBaseName in self.cachedAgentSubscriptions:
            return self.cachedAgentSubscriptions.get(agentBaseName)

        newSubcrp = AgentSubscription(
            agentBaseName, self.propertyGenerator, self.client
        )

        self.cachedAgentSubscriptions[agentBaseName] = newSubcrp
        return newSubcrp

    def getAllRunningAgents(self) -> list[str]:
        if self.allRunningAgents.get() is None:
            return []
        return self.allRunningAgents.get()

    def getCurrentlyRunningAgents(self) -> list[str]:
        if self.currentRunningAgents.get() is None:
            return []
        return self.currentRunningAgents.get()


class AgentSubscription:
    TIMERBASE = Agent.TIMERS
    TIMERSUBBASES = [
        AgentOperator.CREATETIMER,
        AgentOperator.PERIODICTIMER,
        AgentOperator.SHUTDOWNTIMER,
        AgentOperator.CLOSETIMER,
    ]

    def __init__(
        self,
        agentBaseName: str,
        propertyGenerator: PropertyOperator,
        client: XTablesClient,
    ) -> None:
        self.timerSubs = {}
        for timerSub in self.TIMERSUBBASES:
            table = f"{agentBaseName}.{self.TIMERBASE}.{timerSub}_Ms:"
            self.timerSubs[timerSub] = self._getSub(
                propertyGenerator, table, client.getDouble, -1
            )

        self.statusSub = self._getSub(
            propertyGenerator,
            f"{agentBaseName}.{AgentOperator.STATUS}",
            client.getString,
            "...",
        )
        self.descriptionSub = self._getSub(
            propertyGenerator,
            f"{agentBaseName}.{AgentOperator.DESCRIPTION}",
            client.getString,
            "...",
        )
        self.errorsSub = self._getSub(
            propertyGenerator,
            f"{agentBaseName}.{AgentOperator.ERRORS}",
            client.getString,
            "none...",
        )
        self.capabilitesSub = self._getSub(
            propertyGenerator,
            f"{agentBaseName}.{AgentOperator.CAPABILITES}",
            client.getStringList,
            "...",
        )

        self.streamPaths = self._getSub(
            propertyGenerator, f"{agentBaseName}.streamPaths", client.getStringList, []
        )
        self.logIP = self._getSub(
            propertyGenerator, f"{agentBaseName}.logIP", client.getString, None
        )
        self.streamW = propertyGenerator.createReadExistingNetworkValueProperty(
            f"{agentBaseName}.stream.width", None
        )
        self.streamH = propertyGenerator.createReadExistingNetworkValueProperty(
            f"{agentBaseName}.stream.height", None
        )

    @staticmethod
    def _getSub(
        propertyGenerator: PropertyOperator,
        table: str,
        defaultGetter,
        default: str = None,
    ):
        networkDefault = defaultGetter(table)

        if networkDefault is None:
            networkDefault = default

        return propertyGenerator.createReadExistingNetworkValueProperty(
            table, networkDefault
        )

    def getTimer(self, timerSubName: str) -> float:
        if timerSubName in self.timerSubs:
            return self.timerSubs.get(timerSubName).get()
        return None

    def getStatus(self) -> str:
        return self.statusSub.get()

    def getDescription(self) -> str:
        return self.descriptionSub.get()

    def getErrors(self) -> str:
        return self.errorsSub.get()

    def getCapabilities(self) -> list[str]:
        return self.capabilitesSub.get()

    def getStreamPaths(self) -> list[list[str,str]]:
        return [path.split("|") for path in self.streamPaths.get()]

    def getLogIp(self) -> str:
        return self.logIP.get()
