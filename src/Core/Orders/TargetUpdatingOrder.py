from abstract.Order import Order
from tools import NtUtils


class TargetUpdatingOrder(Order):
    TARGETKEY = "net-target-key"

    def create(self):
        pass

    def run(self, input):
        target = NtUtils.getPose2dFromBytes(input)
        self.shareOperator.put(
            TargetUpdatingOrder.TARGETKEY, target[:2]
        )  # x,y part until we use rotation

    def getDescription(self):
        return "Updates_network_target"
    
    def getName(self):
        "target_updating_order"
