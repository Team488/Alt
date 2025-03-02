from typing import Any, Optional
from JXTABLES.XTablesClient import XTablesClient

from Core.PropertyOperator import PropertyOperator


class UpdateOperator:
    ALLRUNNINGAGENTPATHS = "ALL_RUNNING_AGENT_PATHS"

    def __init__(self, xclient: XTablesClient, propertyOperator: PropertyOperator):
        self.__xclient = xclient
        self.uniqueUpdateName = propertyOperator.getFullPrefix()[:-1]
        self.addToAllRunning(self.uniqueUpdateName)
        self.__propertyOp = propertyOperator
        self.__subscribedUpdates = set()

    def addToAllRunning(self, uniqueUpdateName):
        existingNames = self.__xclient.getStringList(self.ALLRUNNINGAGENTPATHS)
        if existingNames is None:
            existingNames = []  # "default arg"
        if uniqueUpdateName not in existingNames:
            existingNames.append(uniqueUpdateName)

        self.__xclient.putStringList(self.ALLRUNNINGAGENTPATHS, existingNames)

    def getAllRunning(self) -> list[str]:
        return self.__xclient.getStringList(self.ALLRUNNINGAGENTPATHS)

    def addGlobalUpdate(self, updateName, value) -> None:
        self.__propertyOp.createCustomReadOnlyProperty(
            propertyTable=updateName,
            propertyValue=value,
            addBasePrefix=True,
            addOperatorPrefix=True,
        ).set(value)

    def readGlobalUpdate(self, updateName, default=None, loadIfSaved=True) -> Any:
        return self.__propertyOp.createProperty(
            propertyTable=updateName,
            propertyDefault=default,
            loadIfSaved=loadIfSaved,
            isCustom=True,
            addBasePrefix=True,
            addOperatorPrefix=True,
            setDefaultOnNetwork=False,
        ).get()

    def readAllGlobalUpdates(self, updateName) -> list[str, Any]:
        updates = []
        for runningPath in self.getAllRunning():
            value = self.__propertyOp.createProperty(
                f"{runningPath}.{updateName}",
                propertyDefault=None,
                isCustom=True,
                addBasePrefix=False,
                addOperatorPrefix=False,
                setDefaultOnNetwork=False,
            ).get()
            if value is not None:
                updates.append((runningPath, value))

        return updates

    def setAllGlobalUpdate(self, globalUpdateName, globalUpdateValue):
        for runningPath in self.getAllRunning():
            self.__propertyOp.createCustomReadOnlyProperty(
                f"{runningPath}.{globalUpdateName}",
                propertyValue=None,
                addBasePrefix=False,
                addOperatorPrefix=False,
            ).set(globalUpdateValue)

    def subscribeAllGlobalUpdates(
        self,
        updateName,
        updateSubscriber,
        runOnNewSubscribe=None,
        runOnRemoveSubscribe=None,
    ) -> tuple[list[str]]:
        newSubscribers = []
        runningPaths = self.getAllRunning()
        fullTables = set()
        for runningPath in runningPaths:
            fullTable = f"{runningPath}.{updateName}"
            fullTables.add(fullTable)
            if fullTable in self.__subscribedUpdates:
                # already subscribed to this
                continue

            self.__xclient.subscribe(fullTable, updateSubscriber)
            self.__subscribedUpdates.add(fullTable)
            newSubscribers.append(fullTable)
            if runOnNewSubscribe is not None:
                runOnNewSubscribe(fullTable)

        removedSubscribers = []
        for subscribedPath in self.__subscribedUpdates:
            if subscribedPath not in fullTables:
                self.__xclient.unsubscribe(fullTable, updateSubscriber)
                removedSubscribers.append(subscribedPath)

        for toRemove in removedSubscribers:
            self.__subscribedUpdates.remove(toRemove)
            if runOnRemoveSubscribe is not None:
                runOnRemoveSubscribe(fullTable)

        return newSubscribers, removedSubscribers

    def unsubscribeToAllGlobalUpdates(self, updateName, updateSubscriber):
        runningPaths = self.getAllRunning()
        for runningPath in runningPaths:
            fullTable = f"{runningPath}.{updateName}"

            self.__xclient.unsubscribe(fullTable, updateSubscriber)

    def deregister(self):
        existingNames: list = self.__xclient.getStringList(self.ALLRUNNINGAGENTPATHS)
        if existingNames is None:
            existingNames = []  # "default arg"
        else:
            if self.uniqueUpdateName in existingNames:
                existingNames.remove(self.uniqueUpdateName)

        self.__xclient.putStringList(self.ALLRUNNINGAGENTPATHS, existingNames)
