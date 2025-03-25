"""
Order management system that executes one-time operations in response to network triggers.

This module provides the OrderOperator class which manages the registration and execution
of Order objects. Orders are one-time operations that can be triggered via network
messages through XTables. The system handles creating triggers, tracking active orders,
and reporting execution status.
"""

import traceback
from logging import Logger
from typing import Any, Set, Callable, Dict, Protocol, TypeVar, cast
from JXTABLES.XTablesClient import XTablesClient
from abstract.Order import Order
from Core.PropertyOperator import PropertyOperator, ReadonlyProperty
from Core.TimeOperator import Timer

# Return type from XTablesClient subscription callback
class XTableReturn(Protocol):
    """
    Protocol defining the return type from XTablesClient subscription callbacks.
    
    Attributes:
        key: The table key that was updated
        value: The new value for the table
        type: The data type identifier for the value
    """
    key: str
    value: Any
    type: int

# subscribes to command request with xtables and then executes when requested
class OrderOperator:
    """
    Manages the registration and execution of one-time operations (Orders).
    
    This class enables creating network-triggered one-time operations. When a specific
    network table receives a value, the associated Order object is executed. The system
    tracks and reports the status of each order execution, providing timing information
    and error handling.
    
    Attributes:
        Sentinel: Logger for recording order operations
        propertyOp: PropertyOperator for reporting order status
        triggers: Set of active trigger names
    """
    def __init__(
        self, xclient: XTablesClient, propertyOp: PropertyOperator, logger: Logger
    ) -> None:
        """
        Initialize an OrderOperator with required dependencies.
        
        Args:
            xclient: XTablesClient for network communication
            propertyOp: PropertyOperator for reporting order status
            logger: Logger for recording order operations
        """
        self.Sentinel: Logger = logger
        self.propertyOp: PropertyOperator = propertyOp
        self.triggers: Set[str] = set()
        self.__xclient: XTablesClient = xclient
        self.__setTriggerDescription: Callable[[str, str], bool] = lambda orderTriggerName, description: self.propertyOp.createCustomReadOnlyProperty(
            f"active_triggers.{orderTriggerName}.Description", description
        ).set(
            description
        )
        self.__setTriggerStatus: Callable[[str, str], bool] = lambda orderTriggerName, status: self.propertyOp.createCustomReadOnlyProperty(
            f"active_triggers.{orderTriggerName}.Status", status
        ).set(
            status
        )

    def __runOrder(self, order: Order, ret: XTableReturn) -> None:
        """
        Execute an order in response to a network trigger.
        
        This private method runs the order's execution lifecycle (run and cleanup phases),
        updates the trigger status, and handles any exceptions that occur during execution.
        
        Args:
            order: The Order object to execute
            ret: The XTableReturn containing the trigger information and input value
        """
        orderTriggerName: str = ret.key
        self.__setTriggerStatus(orderTriggerName, "running!")
        self.Sentinel.info(f"Starting order that does: {order.getDescription()}")
        timer: Timer = order.getTimer()
        try:
            self.Sentinel.debug(f"Running order...")
            progressStr: str = "run"
            with timer.run("run"):
                order.run(input=ret.value)

            self.Sentinel.debug(f"Cleanup order...")
            progressStr = "cleanup"
            with timer.run("cleanup"):
                order.cleanup()

            self.__setTriggerStatus(orderTriggerName, f"sucessfully run!")
        except Exception as e:
            self.__setTriggerStatus(
                orderTriggerName, f"failed!\n On {progressStr}: {e}"
            )
            tb: str = traceback.format_exc()
            self.Sentinel.error(tb)

    def createOrderTrigger(self, orderTriggerName: str, orderToRun: Order) -> None:
        """
        Register an Order to be executed when a specific network trigger is received.
        
        This method sets up the order, initializes it, and subscribes to the specified
        network table to execute the order when a value is received. It also broadcasts
        information about the order to network tables for monitoring purposes.
        
        Args:
            orderTriggerName: The network table name to use as a trigger
            orderToRun: The Order object to execute when triggered
        """
        # broadcast order and what it does
        self.__setTriggerDescription(orderTriggerName, orderToRun.getDescription())
        self.__setTriggerStatus(orderTriggerName, "waiting to run")

        # running create
        with orderToRun.getTimer().run("create"):
            orderToRun.create()

        # subscribing to trigger
        self.__xclient.subscribe(
            orderTriggerName, lambda ret: self.__runOrder(orderToRun, ret)
        )
        self.triggers.add(orderTriggerName)
        # assign the order order
        self.Sentinel.info(
            f"Created order trigger | Trigger Name: {orderTriggerName} Order description: {orderToRun.getDescription()}"
        )

    def deregister(self) -> bool:
        """
        Unsubscribe from all registered order triggers.
        
        This method is typically called during shutdown to clean up all subscriptions.
        
        Returns:
            True if all triggers were successfully removed, False otherwise
        """
        wasAllRemoved: bool = True
        for orderTriggerName in self.triggers:
            wasAllRemoved &= self.__xclient.unsubscribe(
                orderTriggerName, self.__runOrder
            )
        self.triggers.clear()
        return wasAllRemoved
