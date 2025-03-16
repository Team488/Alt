from logging import Logger
from threading import Lock
from typing import Any, Optional
from JXTABLES.XTablesClient import XTablesClient
from Core.Central import Central
from Core.PropertyOperator import PropertyOperator, ReadonlyProperty
from Core.ConfigOperator import ConfigOperator
from Core.ShareOperator import ShareOperator


class XDashOperator:
    """Telemetry manager for XDash"""

    def __init__(
        self,
        central: Central,
        xclient: XTablesClient,
        propertyOperator: PropertyOperator,
        configOperator: ConfigOperator,
        shareOperator: ShareOperator,
        logger: Logger,
    ) -> None:
        self.central: Central = central
        self.xclient: XTablesClient = xclient
        self.propertyOperator: PropertyOperator = propertyOperator
        self.configOperator: ConfigOperator = configOperator
        self.shareOp: ShareOperator = shareOperator
        self.Sentinel: Logger = logger

        # telemetry properties
        self.mapProp: ReadonlyProperty = self.propertyOperator.createCustomReadOnlyProperty("Probmap", "")
        self.pathProp: ReadonlyProperty = self.propertyOperator.createCustomReadOnlyProperty(
            "Best_Path", ""
        )

    def __sendMapUpdate(self) -> None:
        # do stuff
        self.mapProp.set("value here")

    def __sendPathUpdate(self) -> None:
        # do stuff
        self.mapProp.set("path here")

    def run(self) -> None:
        # loop
        self.__sendMapUpdate()
        self.__sendPathUpdate()
        # etc etc
