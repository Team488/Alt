from logging import Logger
from threading import Lock
from JXTABLES.XTablesClient import XTablesClient
from Core.Central import Central
from Core.PropertyOperator import PropertyOperator
from Core.ConfigOperator import ConfigOperator
from Core.ShareOperator import ShareOperator

class XDashOperator:
    """ Telemetry manager for XDash  """
    def __init__(self, central : Central, xclient : XTablesClient, propertyOperator : PropertyOperator, configOperator : ConfigOperator, shareOperator : ShareOperator, logger : Logger):
        self.central = central
        self.xclient = xclient
        self.propertyOperator = propertyOperator
        self.configOperator = configOperator
        self.shareOp = shareOperator
        self.Sentinel = logger
        
        # telemetry properties
        self.mapProp = self.propertyOperator.createCustomReadOnlyProperty("Probmap","")
        self.pathProp = self.propertyOperator.createCustomReadOnlyProperty("Best_Path","")

    def __sendMapUpdate(self):
        # do stuff
        self.mapProp.set("value here")

    def __sendPathUpdate(self):
         # do stuff
        self.mapProp.set("path here")

    def run(self):
        # loop
        self.__sendMapUpdate()
        self.__sendPathUpdate()
        # etc etc


