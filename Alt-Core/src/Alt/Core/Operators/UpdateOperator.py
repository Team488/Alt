import random
import time
from collections import defaultdict
from typing import Any, Callable, Optional, Dict, Set, List, Tuple, DefaultDict
from JXTABLES.XTablesClient import XTablesClient
from .PropertyOperator import Property, PropertyOperator
from .LogOperator import getChildLogger

Sentinel = getChildLogger("Update_Operator")


class UpdateOperator:
    ALLRUNNINGAGENTPATHS: str = "ALL_RUNNING_AGENT_PATHS"
    ALLPATHLOCK: str = "ALL_RUNNING_AGENT_PATHS.IDLOCK"
    CURRENTLYRUNNINGAGENTPATHS: str = "CURRENTLY_RUNNING_AGENT_PATHS"
    CURRENTPATHLOCK: str = "CURRENTLY_RUNNING_AGENT_PATHS.IDLOCK"
    EMPTYLOCK: int = -1
    BUSYLOCK: int = 1

    def __init__(
        self, xclient: XTablesClient, propertyOperator: PropertyOperator
    ) -> None:
        self.__xclient: XTablesClient = xclient
        self.uniqueUpdateName: str = propertyOperator.getFullPrefix()
        self.addToRunning(self.uniqueUpdateName)
        self.__propertyOp: PropertyOperator = propertyOperator
        self.__subscribedUpdates: DefaultDict[str, Set[str]] = defaultdict(set)
        self.__subscribedRunOnClose: Dict[str, Optional[Callable[[str], None]]] = {}
        self.__subscribedSubscriber: Dict[str, Callable[[Any], None]] = {}

    def withLock(self, runnable: Callable[[], None], isAllRunning: bool):
        PATHLOCK = self.ALLPATHLOCK if isAllRunning else self.CURRENTPATHLOCK

        # add uniform random delay to avoid collision in reading empty lock. need a much better method for atomic operations over the network
        delay = random.uniform(0, 0.1)  # max 100ms
        time.sleep(delay)

        if self.__xclient.getDouble(PATHLOCK) != None:
            while self.__xclient.getDouble(PATHLOCK) != self.EMPTYLOCK:
                time.sleep(0.01)  # wait for lock to open

        self.__xclient.putDouble(PATHLOCK, self.BUSYLOCK)
        try:
            runnable()
        except Exception as e:
            Sentinel.fatal(e)
        finally:
            self.__xclient.putDouble(PATHLOCK, self.EMPTYLOCK)

    def addToRunning(self, uniqueUpdateName: str) -> None:
        """Add this agent's unique update name to the list of all running agents"""

        def add(isAllRunning: bool):
            RUNNINGPATH = (
                self.ALLRUNNINGAGENTPATHS
                if isAllRunning
                else self.CURRENTLYRUNNINGAGENTPATHS
            )
            existingNames = self.__xclient.getStringList(RUNNINGPATH)
            if existingNames is None:
                existingNames = []  # "default arg"
            if uniqueUpdateName not in existingNames:
                existingNames.append(uniqueUpdateName)

            self.__xclient.putStringList(RUNNINGPATH, existingNames)

        addAll = lambda: add(True)
        addCur = lambda: add(False)

        self.withLock(addAll, isAllRunning=True)  # always add to all running
        self.withLock(addCur, isAllRunning=False)  # also always add to current running

    def getCurrentlyRunning(
        self, pathFilter: Optional[Callable[[str], bool]] = None
    ) -> List[str]:
        """Get a list of currently running agent paths, optionally filtered"""
        stringList = self.__xclient.getStringList(self.ALLRUNNINGAGENTPATHS)
        if stringList is None:
            return []

        runningPaths = [
            runningPath
            for runningPath in stringList
            if pathFilter is None or pathFilter(runningPath)
        ]
        return runningPaths

    def addGlobalUpdate(self, updateName: str, value: Any) -> None:
        """Add a global update with the given name and value"""
        self.__propertyOp.createCustomReadOnlyProperty(
            propertyTable=updateName,
            propertyValue=value,
            addBasePrefix=True,
            addOperatorPrefix=True,
        ).set(value)

    def createGlobalUpdate(
        self, updateName: str, default: Any = None, loadIfSaved: bool = True
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
        self, updateName: str, pathFilter: Optional[Callable[[str], bool]] = None
    ) -> List[Tuple[str, Any]]:
        """Read global updates with the given name from all running agents"""
        updates: List[Tuple[str, Any]] = []
        for runningPath in self.getCurrentlyRunning(pathFilter):
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
        globalUpdateName: str,
        globalUpdateValue: Any,
        pathFilter: Optional[Callable[[str], bool]] = None,
    ) -> None:
        """Set a global update with the given name and value for all running agents"""
        for runningPath in self.getCurrentlyRunning(pathFilter):
            self.__propertyOp.createCustomReadOnlyProperty(
                f"{runningPath}.{globalUpdateName}",
                propertyValue=None,
                addBasePrefix=False,
                addOperatorPrefix=False,
            ).set(globalUpdateValue)

    def subscribeAllGlobalUpdates(
        self,
        updateName: str,
        updateSubscriber: Callable[[Any], None],
        runOnNewSubscribe: Optional[Callable[[str], None]] = None,
        runOnRemoveSubscribe: Optional[Callable[[str], None]] = None,
        pathFilter: Optional[Callable[[str], bool]] = None,
    ) -> Tuple[List[str], List[str]]:
        """
        Subscribe to global updates with the given name from all running agents

        Args:
            updateName: The name of the update to subscribe to
            updateSubscriber: Callback function to handle update notifications
            runOnNewSubscribe: Optional callback to run when new subscriptions are added
            runOnRemoveSubscribe: Optional callback to run when subscriptions are removed
            pathFilter: Optional filter to apply to running agent paths

        Returns:
            Tuple of (new_subscribers, removed_subscribers)
        """
        newSubscribers: List[str] = []
        runningPaths = self.getCurrentlyRunning(pathFilter)
        fullTables: Set[str] = set()
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

        removedSubscribers: List[str] = []
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
        self,
        updateName: str,
        updateSubscriber: Callable[[Any], None],
        pathFilter: Optional[Callable[[str], bool]] = None,
    ) -> None:
        """
        Unsubscribe from global updates with the given name from all running agents

        Args:
            updateName: The name of the update to unsubscribe from
            updateSubscriber: The subscriber callback that was used to subscribe
            pathFilter: Optional filter to apply to running agent paths
        """
        runningPaths = self.getCurrentlyRunning(pathFilter)
        for runningPath in runningPaths:
            fullTable = f"{runningPath}.{updateName}"
            self.__xclient.unsubscribe(fullTable, updateSubscriber)

    def deregister(self) -> None:
        """Deregister this agent and clean up all subscriptions"""

        def remove():
            existingNames = self.__xclient.getStringList(
                self.CURRENTLYRUNNINGAGENTPATHS
            )
            if existingNames is None:
                existingNames = []  # "default arg"
            else:
                if self.uniqueUpdateName in existingNames:
                    existingNames.remove(self.uniqueUpdateName)

            self.__xclient.putStringList(self.CURRENTLYRUNNINGAGENTPATHS, existingNames)

        self.withLock(
            remove, isAllRunning=False
        )  # only currently running removes paths

        for updateName, fullTables in self.__subscribedUpdates.items():
            runOnClose = self.__subscribedRunOnClose.get(updateName)
            subscriber = self.__subscribedSubscriber.get(updateName)

            if subscriber is None:
                continue

            for fullTable in fullTables:
                self.__xclient.unsubscribe(fullTable, subscriber)

                if runOnClose is not None:
                    runOnClose(fullTable)
