# an order, otherwise known as a command will be triggered and then run once.
# lifespan: 1. create 2. run 3. close
# NOTE: Orders will get processwide "shared" objects passed in via init.
# For things pertaining only to the order, create them in the create method

from abc import ABC, abstractmethod
from typing import Any, Optional

from JXTABLES.XTablesClient import XTablesClient
from ..Operators.PropertyOperator import PropertyOperator
from ..Operators.ConfigOperator import ConfigOperator
from ..Operators.ShareOperator import ShareOperator
from ..Operators.TimeOperator import Timer


class Order(ABC):
    def __init__(self) -> None:
        self.xclient: Optional[XTablesClient] = None
        self.propertyOperator: Optional[PropertyOperator] = None
        self.configOperator: Optional[ConfigOperator] = None
        self.shareOperator: Optional[ShareOperator] = None
        self.timer: Optional[Timer] = None

    def inject(
        self,
        xclient: XTablesClient,
        propertyOperator: PropertyOperator,
        configOperator: ConfigOperator,
        shareOperator: ShareOperator,
        timer: Timer,
    ) -> None:
        """ "Injects" arguments into the order. Should not be modified in any subclasses"""
        self.xclient = xclient
        self.propertyOperator = propertyOperator
        self.configOperator = configOperator
        self.shareOperator = shareOperator
        self.timer = timer

    def getTimer(self) -> Timer:
        """Use only when needed, and only when associated with order"""
        if self.timer is None:
            raise ValueError("Timer not initialized")
        return self.timer
    
    @classmethod
    def getName(cls) -> str:
        """Return Order Name"""
        return cls.__name__

    @abstractmethod
    def create(self) -> None:
        """Perform any one time creation here.\n
        NOTE: this will not be called multiple times, even if the order is run multiple times"""
        pass

    @abstractmethod
    def run(self, inputVal: Any) -> Any:
        """Put your run once code here"""
        pass

    @abstractmethod
    def getDescription(self) -> str:
        """Return Concise Order Description"""
        pass

    def cleanup(self) -> None:
        """Optional Method: Cleanup after running order"""
        pass