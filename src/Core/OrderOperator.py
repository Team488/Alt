import traceback
from logging import Logger
from JXTABLES.XTablesClient import XTablesClient
from abstract.Order import Order

# subscribes to command request with xtables and then executes when requested
class OrderOperator:
    def __init__(self,xclient : XTablesClient, logger : Logger):
        self.Sentinel = logger
        self.__xclient : XTablesClient = xclient
        self.__orderMap = {}
        self.__getTriggerName = lambda orderTriggerName : f"triggers.{orderTriggerName}.Name"
        self.__getTriggerStatus = lambda orderTriggerName : f"triggers.{orderTriggerName}.Status"

    
    def __runOrder(self, ret):
        orderTriggerName = ret.key
        order : Order = self.__orderMap.get(orderTriggerName)
        if order == None:
            self.__xclient.putString(self.__getTriggerStatus(orderTriggerName), "invalid trigger!")
            # i dont see this ever happening (unless deregister is called then a run order)
            Sentinel.error("OrderMap does not contain the trigger name expected to run order!")
            return
        
        self.__xclient.putString(self.__getTriggerStatus(orderTriggerName), "running!")
        self.Sentinel.info(f"Starting order that does: {order.getDescription()}")
        
        try:
            self.Sentinel.debug(f"Creating order...")
            progressStr = "create"
            order.create()
            
            self.Sentinel.debug(f"Running order...")
            progressStr = "run"
            order.run()
            
            self.Sentinel.debug(f"Closing order...")
            progressStr = "close"
            order.close()

            self.__xclient.putString(self.__getTriggerStatus(orderTriggerName), f"sucessfully run!")
        except Exception as e:
            self.__xclient.putString(self.__getTriggerStatus(orderTriggerName), f"failed!\n On {progressStr}: {e}")
            tb = traceback.format_exc()
            self.Sentinel.error(tb)

    
    def createOrder(self, orderTriggerName : str, orderToRun : Order):
        # broadcast order and what it does
        self.__xclient.putString(self.__getTriggerName(orderTriggerName), orderToRun.getDescription())
        self.__xclient.putString(self.__getTriggerStatus(orderTriggerName), "waiting to run")
        # subscribing to trigger
        self.__xclient.subscribe(orderTriggerName,self.__runOrder)
        # assign the order order
        self.__orderMap[orderTriggerName] = orderToRun
        self.Sentinel.info(f"Created order trigger | Trigger Name: {orderTriggerName} Order description: {orderToRun.getDescription()}")
        
    
    def deregister(self):
        self.__xclient.unsubscribe_all(self.__runOrder)
        self.__orderMap.clear()





