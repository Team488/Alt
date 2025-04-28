"""
UpdateOperator Module.

This module defines the `UpdateOperator` class, responsible for managing global updates 
across multiple running agents. It facilitates adding, subscribing, and deregistering 
updates while ensuring that conflicts are minimized through locking mechanisms.
"""

import random
import time
from collections import defaultdict
from typing import Any, Callable, Optional, Dict, Set, List, Tuple, DefaultDict
from JXTABLES.XTablesClient import XTablesClient
from .PropertyOperator import Property, PropertyOperator
from .LogOperator import getChildLogger

Sentinel = getChildLogger("Update_Operator")

class UpdateOperator:
    """
    Manages global updates for multiple agents.

    The `UpdateOperator` class provides functionalities to create, set, 
    and get global updates among agents. It handles subscriptions to updates 
    and ensures there are no conflicts in the updates being processed 
    by employing locking mechanisms.

    Attributes:
        ALLRUNNINGAGENTPATHS (str): Path to retrieve all running agent paths.
        ALLPATHLOCK (str): Lock identifier for all running agents.
        CURRENTLYRUNNINGAGENTPATHS (str): Path to retrieve currently running agent paths.
        CURRENTPATHLOCK (str): Lock identifier for currently running agents.
        EMPTYLOCK (int): Constant representing an empty lock state.
        BUSYLOCK (int): Constant representing a busy lock state.
    """

    ALLRUNNINGAGENTPATHS: str = "ALL_RUNNING_AGENT_PATHS"
    ALLPATHLOCK: str = "ALL_RUNNING_AGENT_PATHS.IDLOCK"
    CURRENTLYRUNNINGAGENTPATHS: str = "CURRENTLY_RUNNING_AGENT_PATHS"
    CURRENTPATHLOCK: str = "CURRENTLY_RUNNING_AGENT_PATHS.IDLOCK"
    EMPTYLOCK: int = -1
    BUSYLOCK: int = 1

    def __init__(self, xclient: XTablesClient, propertyOperator: PropertyOperator) -> None:
        """Initializes the UpdateOperator with the given XTablesClient and PropertyOperator.

        Args:
            xclient (XTablesClient): The XTables client instance to interact with.
            propertyOperator (PropertyOperator): The property operator instance for managing properties.
        """
        self.__xclient: XTablesClient = xclient
        self.uniqueUpdateName: str = propertyOperator.getFullPrefix()
        self.addToRunning(self.uniqueUpdateName)
        self.__propertyOp: PropertyOperator = propertyOperator
        self.__subscribedUpdates: DefaultDict[str, Set[str]] = defaultdict(set)
        self.__subscribedRunOnClose: Dict[str, Optional[Callable[[str], None]]] = {}
        self.__subscribedSubscriber: Dict[str, Callable[[Any], None]] = {}

    def withLock(self, runnable: Callable[[], None], isAllRunning: bool) -> None:
        """Executes a callable with a lock to ensure exclusive access.

        Args:
            runnable (Callable[[], None]): The callable to be executed with the lock.
            isAllRunning (bool): Determines whether to use the all running agents lock or current running agents lock.

        Raises:
            Exception: Propagates any exception thrown by the runnable.
        """
        PATHLOCK = self.ALLPATHLOCK if isAllRunning else self.CURRENTPATHLOCK
        # Add uniform random delay to avoid collision in reading empty lock.
        delay = random.uniform(0, 0.1)  # Max 100ms
        time.sleep(delay)
        
        if self.__xclient.getDouble(PATHLOCK) is not None:
            while self.__xclient.getDouble(PATHLOCK) != self.EMPTYLOCK:
                time.sleep(0.01)  # Wait for lock to open

        self.__xclient.putDouble(PATHLOCK, self.BUSYLOCK)
        
        try:
            runnable()
        except Exception as e:
            Sentinel.fatal(e)
        finally:
            self.__xclient.putDouble(PATHLOCK, self.EMPTYLOCK)

    def addToRunning(self, uniqueUpdateName: str) -> None:
        """Adds the agent's unique update name to the list of running agents.

        Args:
            uniqueUpdateName (str): The unique update name to be added to the running agents list.
        """
        def add(isAllRunning: bool):
            RUNNINGPATH = (
                self.ALLRUNNINGAGENTPATHS
                if isAllRunning
                else self.CURRENTLYRUNNINGAGENTPATHS
            )
            existingNames = self.__xclient.getStringList(RUNNINGPATH)
            if existingNames is None:
                existingNames = []  # Default arg
            if uniqueUpdateName not in existingNames:
                existingNames.append(uniqueUpdateName)
            self.__xclient.putStringList(RUNNINGPATH, existingNames)
        
        addAll = lambda: add(True)
        addCur = lambda: add(False)
        self.withLock(addAll, isAllRunning=True)  # Always add to all running
        self.withLock(addCur, isAllRunning=False)  # Also always add to current running

    def getCurrentlyRunning(self, pathFilter: Optional[Callable[[str], bool]] = None) -> List[str]:
        """Gets a filtered list of currently running agent paths.

        Args:
            pathFilter (Callable[[str], bool], optional): A callable to filter the running paths.

        Returns:
            List[str]: A list of currently running agent paths (filtered if a filter is provided).
        """
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
        """Adds a global update with a specified name and value.

        Args:
            updateName (str): The name of the global update.
            value (Any): The value to associate with the global update.
        """
        self.__propertyOp.createCustomReadOnlyProperty(
            propertyTable=updateName,
            propertyValue=value,
            addBasePrefix=True,
            addOperatorPrefix=True,
        ).set(value)

    def createGlobalUpdate(self, updateName: str, default: Any = None, loadIfSaved: bool = True) -> Property:
        """Creates a global update with a specified name, default value, and load options.

        Args:
            updateName (str): The name of the global update.
            default (Any, optional): The default value of the update. Defaults to None.
            loadIfSaved (bool, optional): Whether to load the value if it was saved. Defaults to True.

        Returns:
            Property: The created global property.
        """
        return self.__propertyOp._createProperty(
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
        """Reads global updates with the specified name from all running agents.

        Args:
            updateName (str): The name of the update to read.
            pathFilter (Callable[[str], bool], optional): A callable to filter the running paths.

        Returns:
            List[Tuple[str, Any]]: A list of tuples containing the running path and its associated value.
        """
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
        """Sets a global update with a specified name and value for all running agents.

        Args:
            globalUpdateName (str): The name of the global update.
            globalUpdateValue (Any): The value to set for the global update.
            pathFilter (Callable[[str], bool], optional): Optional filter to apply to running agent paths.
        """
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
        """Subscribes to global updates with the specified name from all running agents.

        Args:
            updateName (str): The name of the update to subscribe to.
            updateSubscriber (Callable[[Any], None]): The callback function to handle update notifications.
            runOnNewSubscribe (Callable[[str], None], optional): Optional callback for new subscriptions.
            runOnRemoveSubscribe (Callable[[str], None], optional): Optional callback for removed subscriptions.
            pathFilter (Callable[[str], bool], optional): Optional filter for running agent paths.

        Returns:
            Tuple[List[str], List[str]]: A tuple containing lists of newly subscribed and removed subscribers.
        """
        newSubscribers: List[str] = []
        runningPaths = self.getCurrentlyRunning(pathFilter)
        fullTables: Set[str] = set()
        
        for runningPath in runningPaths:
            fullTable = f"{runningPath}.{updateName}"
            fullTables.add(fullTable)
            if fullTable in self.__subscribedUpdates[updateName]:
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
        """Unsubscribes from global updates with the specified name from all running agents.

        Args:
            updateName (str): The name of the update to unsubscribe from.
            updateSubscriber (Callable[[Any], None]): The subscriber callback used during subscription.
            pathFilter (Callable[[str], bool], optional): Optional filter for running agent paths.
        """
        runningPaths = self.getCurrentlyRunning(pathFilter)
        for runningPath in runningPaths:
            fullTable = f"{runningPath}.{updateName}"
            self.__xclient.unsubscribe(fullTable, updateSubscriber)

    def deregister(self) -> None:
        """Deregisters the agent and cleans up all subscriptions."""
        def remove():
            existingNames = self.__xclient.getStringList(
                self.CURRENTLYRUNNINGAGENTPATHS
            )
            if existingNames is None:
                existingNames = []  # Default arg
            else:
                if self.uniqueUpdateName in existingNames:
                    existingNames.remove(self.uniqueUpdateName)
            self.__xclient.putStringList(self.CURRENTLYRUNNINGAGENTPATHS, existingNames)

        self.withLock(remove, isAllRunning=False)  # Only currently running removes paths
        
        for updateName, fullTables in self.__subscribedUpdates.items():
            runOnClose = self.__subscribedRunOnClose.get(updateName)
            subscriber = self.__subscribedSubscriber.get(updateName)
            if subscriber is None:
                continue
            for fullTable in fullTables:
                self.__xclient.unsubscribe(fullTable, subscriber)
                if runOnClose is not None:
                    runOnClose(fullTable)