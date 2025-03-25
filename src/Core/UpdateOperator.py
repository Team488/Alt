"""
Update Operator Module - Distributed agent communication and notification system

This module provides a mechanism for agents to publish and subscribe to updates across
the distributed system. It manages the registration, deregistration, and notification
of agents, enabling them to share state and coordinate actions with minimal coupling.

The UpdateOperator serves as a publish-subscribe system where:
- Agents can register themselves as running components
- Updates can be published globally or to specific agents
- Agents can subscribe to updates from other agents
- Changes are propagated automatically to subscribers

The system uses JXTABLES as the underlying communication mechanism, providing
network transparency so that agents can communicate regardless of whether they
are running on the same process, the same machine, or across a network.

Example usage:
    # Publishing an update
    updateOperator.addGlobalUpdate("object_detected", detection_data)
    
    # Creating a mutable update
    position_update = updateOperator.createGlobalUpdate("robot_position")
    position_update.set(new_position)
    
    # Subscribing to updates from all agents
    def handle_detection(detection_data):
        # Process new detection data
        pass
        
    updateOperator.subscribeAllGlobalUpdates("object_detected", handle_detection)
"""

from typing import Any, Callable, Optional, Dict, Set, List, Tuple, Union, DefaultDict
from JXTABLES.XTablesClient import XTablesClient

from Core.PropertyOperator import Property, PropertyOperator, ReadonlyProperty
from collections import defaultdict


class UpdateOperator:
    """
    Manages update notifications and subscriptions between distributed agents.
    
    The UpdateOperator provides a system for agents to publish and subscribe to
    updates across the distributed system using JXTABLES as the underlying
    communication mechanism. It tracks running agents and manages their
    registration, deregistration, and notifications.
    
    Attributes:
        ALLRUNNINGAGENTPATHS: Key used to store the list of all running agent paths
        uniqueUpdateName: Unique identifier for this agent in the update system
    """
    
    ALLRUNNINGAGENTPATHS: str = "ALL_RUNNING_AGENT_PATHS"

    def __init__(self, xclient: XTablesClient, propertyOperator: PropertyOperator) -> None:
        """
        Initialize a new UpdateOperator.
        
        Args:
            xclient: XTablesClient instance for communication
            propertyOperator: PropertyOperator for managing properties
        """
        self.__xclient: XTablesClient = xclient
        self.uniqueUpdateName: str = propertyOperator.getFullPrefix()[:-1]
        self.addToAllRunning(self.uniqueUpdateName)
        self.__propertyOp: PropertyOperator = propertyOperator
        self.__subscribedUpdates: DefaultDict[str, Set[str]] = defaultdict(set)
        self.__subscribedRunOnClose: Dict[str, Optional[Callable[[str], None]]] = {}
        self.__subscribedSubscriber: Dict[str, Callable[[Any], None]] = {}

    def addToAllRunning(self, uniqueUpdateName: str) -> None:
        """
        Register an agent in the global list of running agents.
        
        Adds the specified agent name to the list of all running agents in the system.
        If the agent is already registered, it won't be added again.
        
        Args:
            uniqueUpdateName: The unique identifier of the agent to register
        """
        existingNames = self.__xclient.getStringList(self.ALLRUNNINGAGENTPATHS)
        if existingNames is None:
            existingNames = []  # "default arg"
        if uniqueUpdateName not in existingNames:
            existingNames.append(uniqueUpdateName)

        self.__xclient.putStringList(self.ALLRUNNINGAGENTPATHS, existingNames)

    def getAllRunning(self, pathFilter: Optional[Callable[[str], bool]] = None) -> List[str]:
        """
        Get a list of all currently running agents.
        
        Returns a list of all registered agent paths. Optionally filters the list
        using the provided filter function.
        
        Args:
            pathFilter: Optional function that takes an agent path and returns
                        a boolean indicating whether to include it
                        
        Returns:
            A list of agent paths that are currently running and match the filter
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
        """
        Publish a read-only global update with the given name and value.
        
        Creates a read-only property that can be observed by other agents.
        
        Args:
            updateName: The name of the update to publish
            value: The value to publish with this update
        """
        self.__propertyOp.createCustomReadOnlyProperty(
            propertyTable=updateName,
            propertyValue=value,
            addBasePrefix=True,
            addOperatorPrefix=True,
        ).set(value)

    def createGlobalUpdate(
        self, updateName: str, default: Any = None, loadIfSaved: bool = True
    ) -> Property:
        """
        Create a mutable global update property.
        
        Creates and returns a Property that can be modified and observed by other agents.
        
        Args:
            updateName: The name of the update property to create
            default: Default value for the property if none exists
            loadIfSaved: Whether to load the value from persistent storage if available
            
        Returns:
            A Property object that can be used to get/set the update value
        """
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
        """
        Read global updates with the given name from all running agents.
        
        Collects the values of a specific update from all running agents and
        returns them as a list of (agent_path, value) tuples.
        
        Args:
            updateName: The name of the update to read from all agents
            pathFilter: Optional function to filter which agent paths to include
            
        Returns:
            List of tuples containing (agent_path, update_value) for all agents
            with a non-None value for the specified update
        """
        updates: List[Tuple[str, Any]] = []
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
        globalUpdateName: str,
        globalUpdateValue: Any,
        pathFilter: Optional[Callable[[str], bool]] = None,
    ) -> None:
        """
        Set a global update with the given name and value for all running agents.
        
        This method broadcasts an update to all running agents (or a filtered subset)
        by setting the specified property on each agent to the provided value.
        
        Args:
            globalUpdateName: The name of the update to set
            globalUpdateValue: The value to set for the update
            pathFilter: Optional function to filter which agent paths to include
        """
        for runningPath in self.getAllRunning(pathFilter):
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
        runningPaths = self.getAllRunning(pathFilter)
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
        pathFilter: Optional[Callable[[str], bool]] = None
    ) -> None:
        """
        Unsubscribe from global updates with the given name from all running agents.
        
        Removes subscriptions for the specified update from all running agents
        (or a filtered subset) that were previously subscribed to using the
        subscribeAllGlobalUpdates method.
        
        Args:
            updateName: The name of the update to unsubscribe from
            updateSubscriber: The subscriber callback that was used to subscribe
            pathFilter: Optional filter to apply to running agent paths
        """
        runningPaths = self.getAllRunning(pathFilter)
        for runningPath in runningPaths:
            fullTable = f"{runningPath}.{updateName}"
            self.__xclient.unsubscribe(fullTable, updateSubscriber)

    def deregister(self) -> None:
        """
        Deregister this agent and clean up all subscriptions.
        
        Removes this agent from the list of running agents and unsubscribes
        from all notifications. This should be called when the agent is shutting
        down to ensure clean disconnection from the update system.
        
        This method:
        1. Removes the agent from the global running agent list
        2. Unsubscribes from all update notifications
        3. Runs any registered cleanup callbacks
        """
        existingNames = self.__xclient.getStringList(self.ALLRUNNINGAGENTPATHS)
        if existingNames is None:
            existingNames = []  # "default arg"
        else:
            if self.uniqueUpdateName in existingNames:
                existingNames.remove(self.uniqueUpdateName)

        self.__xclient.putStringList(self.ALLRUNNINGAGENTPATHS, existingNames)

        for updateName, fullTables in self.__subscribedUpdates.items():
            runOnClose = self.__subscribedRunOnClose.get(updateName)
            subscriber = self.__subscribedSubscriber.get(updateName)

            if subscriber is None:
                continue

            for fullTable in fullTables:
                self.__xclient.unsubscribe(fullTable, subscriber)

                if runOnClose is not None:
                    runOnClose(fullTable)
