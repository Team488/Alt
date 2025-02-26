# an order, otherwise known as a command will be triggered and then run once.
# lifespan: 1. create 2. run 3. close
# NOTE: Orders will get processwide "shared" objects passed in via init.
# For things pertaining only to the order, create them in the create method

from abc import ABC, abstractmethod
from JXTABLES.XTablesClient import XTablesClient
from Core.Central import Central
from Core.PropertyOperator import PropertyOperator
from Core.ConfigOperator import ConfigOperator
from Core.ShareOperator import ShareOperator
from Core.TimeOperator import Timer


class Order(ABC):
    def __init__(self) -> None:
        pass

    def inject(
        self,
        central: Central,
        xclient: XTablesClient,
        propertyOperator: PropertyOperator,
        configOperator: ConfigOperator,
        shareOperator: ShareOperator,
        timer: Timer,
    ) -> None:
        """ "Injects" arguments into the order. Should not be modified in any subclasses"""
        self.central = central
        self.xclient = xclient
        self.propertyOperator = propertyOperator
        self.configOperator = configOperator
        self.shareOperator = shareOperator
        self.timer = timer

    def getTimer(self):
        """Use only when needed, and only when associated with order"""
        return self.timer

    @abstractmethod
    def create(self):
        """Perform any one time creation here.\n
        NOTE: this will not be called multiple times, even if the order is run multiple times"""
        pass

    @abstractmethod
    def run(self, input):
        """Put your run once code here"""
        pass

    @abstractmethod
    def getDescription(self) -> str:
        """Return Concise Order Description"""
        pass

    def getName(self) -> str:
        """Return Order Name"""
        pass

    def cleanup(self) -> None:
        """Optional Method: Cleanup after running order"""
        pass
