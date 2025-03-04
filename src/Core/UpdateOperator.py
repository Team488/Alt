from typing import Any, Callable, Optional
from JXTABLES.XTablesClient import XTablesClient

from Core.PropertyOperator import Property, PropertyOperator
from collections import defaultdict


class UpdateOperator:
    ALLRUNNINGAGENTPATHS = "ALL_RUNNING_AGENT_PATHS"

    def __init__(self, xclient: XTablesClient, propertyOperator: PropertyOperator):
        self.__xclient = xclient
        self.uniqueUpdateName = propertyOperator.getFullPrefix()[:-1]
        self.addToAllRunning(self.uniqueUpdateName)
        self.__propertyOp = propertyOperator
        self.__subscribedUpdates = defaultdict(set)
        self.__subscribedRunOnClose = {}
        self.__subscribedSubscriber = {}

    def addToAllRunning(self, uniqueUpdateName):
        existingNames = self.__xclient.getStringList(self.ALLRUNNINGAGENTPATHS)
        if existingNames is None:
            existingNames = []  # "default arg"
        if uniqueUpdateName not in existingNames:
            existingNames.append(uniqueUpdateName)

        self.__xclient.putStringList(self.ALLRUNNINGAGENTPATHS, existingNames)

    def getAllRunning(self, pathFilter: Callable[[str], bool] = None) -> list[str]:
        runningPaths = [
            runningPath
            for runningPath in self.__xclient.getStringList(self.ALLRUNNINGAGENTPATHS)
            if pathFilter is None or pathFilter(runningPath)
        ]
        return runningPaths

    def addGlobalUpdate(self, updateName, value) -> None:
        self.__propertyOp.createCustomReadOnlyProperty(
            propertyTable=updateName,
            propertyValue=value,
            addBasePrefix=True,
            addOperatorPrefix=True,
        ).set(value)

    def createGlobalUpdate(
        self, updateName, default=None, loadIfSaved=True
    ) -> Property:
        return self.__propertyOp.createProperty(
            propertyTable=updateName,
            propertyDefault=default,
            loadIfSaved=loadIfSaved,
            isCustom=True,
            addBasePrefix=True,
            addOperatorPrefix=True,
            setDefaultOnNetwork=False,
        )

    def readAllGlobalUpdates(
        self, updateName, pathFilter: Callable[[str], bool] = None
    ) -> list[str, Any]:
        updates = []
        for runningPath in self.getAllRunning(pathFilter):
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

    def setAllGlobalUpdate(
        self,
        globalUpdateName,
        globalUpdateValue,
        pathFilter: Callable[[str], bool] = None,
    ):
        for runningPath in self.getAllRunning(pathFilter):
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
        pathFilter: Callable[[int], bool] = None,
    ) -> tuple[list[str]]:
        newSubscribers = []
        runningPaths = self.getAllRunning(pathFilter)
        fullTables = set()
        for runningPath in runningPaths:
            fullTable = f"{runningPath}.{updateName}"
            fullTables.add(fullTable)
            if fullTable in self.__subscribedUpdates[updateName]:
                # already subscribed to this
                continue

            self.__xclient.subscribe(fullTable, updateSubscriber)
            self.__subscribedUpdates[updateName].add(fullTable)
            newSubscribers.append(fullTable)
            if runOnNewSubscribe is not None:
                runOnNewSubscribe(fullTable)

        removedSubscribers = []
        for subscribedPath in self.__subscribedUpdates[updateName]:
            if subscribedPath not in fullTables:
                self.__xclient.unsubscribe(subscribedPath, updateSubscriber)
                removedSubscribers.append(subscribedPath)

        for toRemovePath in removedSubscribers:
            self.__subscribedUpdates[updateName].remove(toRemovePath)
            if runOnRemoveSubscribe is not None:
                runOnRemoveSubscribe(toRemovePath)

        if updateName not in self.__subscribedRunOnClose.keys():
            self.__subscribedRunOnClose[updateName] = runOnRemoveSubscribe

            self.__subscribedSubscriber[updateName] = updateSubscriber

        return newSubscribers, removedSubscribers

    def unsubscribeToAllGlobalUpdates(
        self, updateName, updateSubscriber, pathFilter: Callable[[str], bool] = None
    ):
        runningPaths = self.getAllRunning(pathFilter)
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

        for updateName, fullTables in self.__subscribedUpdates.items():
            runOnClose = self.__subscribedRunOnClose.get(updateName)
            subscriber = self.__subscribedSubscriber.get(updateName)

            for fullTable in fullTables:

                self.__xclient.unsubscribe(fullTable, subscriber)

                if runOnClose is not None:
                    runOnClose(fullTable)
