import traceback
from logging import Logger
from JXTABLES.XTablesClient import XTablesClient
from abstract.Order import Order
from Core.PropertyOperator import PropertyOperator

# subscribes to command request with xtables and then executes when requested
class OrderOperator:
    def __init__(
        self, xclient: XTablesClient, propertyOp: PropertyOperator, logger: Logger
    ):
        self.Sentinel = logger
        self.propertyOp = propertyOp
        self.triggers = set()
        self.__xclient: XTablesClient = xclient
        self.__setTriggerDescription = lambda orderTriggerName, description: self.propertyOp.createCustomReadOnlyProperty(
            f"active_triggers.{orderTriggerName}.Description", description
        ).set(description)
        self.__setTriggerStatus = lambda orderTriggerName, status: self.propertyOp.createCustomReadOnlyProperty(
            f"active_triggers.{orderTriggerName}.Status", status
        ).set(status)

    def __runOrder(self, order : Order, ret):
        orderTriggerName = ret.key
        self.__setTriggerStatus(orderTriggerName, "running!")
        self.Sentinel.info(f"Starting order that does: {order.getDescription()}")
        timer = order.getTimer()
        try:
            self.Sentinel.debug(f"Running order...")
            progressStr = "run"
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
            tb = traceback.format_exc()
            self.Sentinel.error(tb)

    def createOrderTrigger(self, orderTriggerName: str, orderToRun: Order):
        # broadcast order and what it does
        self.__setTriggerDescription(orderTriggerName, orderToRun.getDescription())
        self.__setTriggerStatus(orderTriggerName, "waiting to run")

        # running create
        with orderToRun.getTimer().run("create"):
                orderToRun.create()
        
        # subscribing to trigger
        self.__xclient.subscribe(orderTriggerName, lambda ret : self.__runOrder(orderToRun, ret))
        self.triggers.add(orderTriggerName)
        # assign the order order
        self.Sentinel.info(
            f"Created order trigger | Trigger Name: {orderTriggerName} Order description: {orderToRun.getDescription()}"
        )

    def deregister(self):
        wasAllRemoved = True
        for orderTriggerName in self.triggers:
            wasAllRemoved &= self.__xclient.unsubscribe(
                orderTriggerName, self.__runOrder
            )
        self.triggers.clear()
        return wasAllRemoved
