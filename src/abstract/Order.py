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

class Order(ABC):
    def __init__(self, central : Central, xclient : XTablesClient, propertyOperator : PropertyOperator, configOperator : ConfigOperator, shareOperator : ShareOperator):
        self.central = central
        self.xclient = xclient
        self.propertyOperator = propertyOperator
        self.configOperator = configOperator
        self.shareOperator = shareOperator
        # other than setting variables, nothing should go here

    @abstractmethod
    def create(self):        
        # perform order init here
        pass

    @abstractmethod
    def run(self, input):
        # order run here
        pass
    
    @abstractmethod
    def close(self):
        # order cleanup here
        pass
    
    @abstractmethod
    def getDescription(self) -> str:
        # return order name here
        pass