# an order, otherwise known as a command will be triggered and then run once.
# lifespan: 1. create 2. run 3. close
# NOTE: Orders will get processwide "shared" objects passed in via init.
# For things pertaining only to the order, create them in the create method

from abc import ABC, abstractmethod
from JXTABLES.XTablesClient import XTablesClient
from Core.Central import Central
from Core.PropertyOperator import PropertyOperator
from Core.ConfigOperator import ConfigOperator

class Order(ABC):
    def __init__(self, central : Central, xclient : XTablesClient, propertyOperator : PropertyOperator, configOperator : ConfigOperator):
        self.central = central
        self.xclient = xclient
        self.propertyOperator = propertyOperator
        self.configOperator = configOperator
        # other than setting variables, nothing should go here

    @abstractmethod
    def create(self):        
        # perform order init here
        pass

    @abstractmethod
    def run(self):
        # order run here
        pass
    
    @abstractmethod
    def close(self):
        # order cleanup here
        pass