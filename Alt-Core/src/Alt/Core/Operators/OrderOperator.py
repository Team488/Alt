import traceback
from typing import Any, Set, Callable, Protocol
from JXTABLES.XTablesClient import XTablesClient
from ..Orders.Order import Order
from .PropertyOperator import PropertyOperator
from .TimeOperator import Timer
from .LogOperator import getChildLogger

Sentinel = getChildLogger("Order_Operator")

# Return type from XTablesClient subscription callback
class XTableReturn(Protocol):
    key: str
    value: Any
    type: int


# subscribes to command request with xtables and then executes when requested
class OrderOperator:
    def __init__(self, xclient: XTablesClient, propertyOp: PropertyOperator) -> None:
        self.propertyOp: PropertyOperator = propertyOp
        self.triggers: Set[str] = set()
        self.__xclient: XTablesClient = xclient
        self.__setTriggerDescription: Callable[
            [str, str], bool
        ] = lambda orderTriggerName, description: self.propertyOp.createCustomReadOnlyProperty(
            f"active_triggers.{orderTriggerName}.Description", description
        ).set(
            description
        )
        self.__setTriggerStatus: Callable[
            [str, str], bool
        ] = lambda orderTriggerName, status: self.propertyOp.createCustomReadOnlyProperty(
            f"active_triggers.{orderTriggerName}.Status", status
        ).set(
            status
        )

    def __runOrder(self, order: Order, ret: XTableReturn) -> None:
        orderTriggerName: str = ret.key
        self.__setTriggerStatus(orderTriggerName, "running!")
        Sentinel.info(f"Starting order that does: {order.getDescription()}")
        timer: Timer = order.getTimer()
        try:
            Sentinel.debug(f"Running order...")
            progressStr: str = "run"
            with timer.run("run"):
                order.run(inputVal=ret.value)

            Sentinel.debug(f"Cleanup order...")
            progressStr = "cleanup"
            with timer.run("cleanup"):
                order.cleanup()

            self.__setTriggerStatus(orderTriggerName, f"sucessfully run!")
        except Exception as e:
            self.__setTriggerStatus(
                orderTriggerName, f"failed!\n On {progressStr}: {e}"
            )
            tb: str = traceback.format_exc()
            Sentinel.error(tb)

    def createOrderTrigger(self, orderTriggerName: str, orderToRun: Order) -> None:
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
        Sentinel.info(
            f"Created order trigger | Trigger Name: {orderTriggerName} Order description: {orderToRun.getDescription()}"
        )

    def deregister(self) -> bool:
        wasAllRemoved: bool = True
        for orderTriggerName in self.triggers:
            wasAllRemoved &= self.__xclient.unsubscribe(
                orderTriggerName, self.__runOrder
            )
        self.triggers.clear()
        return wasAllRemoved
