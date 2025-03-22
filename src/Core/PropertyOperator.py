import logging
from collections.abc import Iterable
from logging import Logger
from typing import Dict, List, Any, Optional, Callable, TypeVar, Union, Tuple, Set, cast
from JXTABLES.XTablesClient import XTablesClient
from JXTABLES import XTableProto_pb2 as XTableProto
from JXTABLES import XTableValues_pb2 as XTableValues
from JXTABLES.XTablesByteUtils import XTablesByteUtils
from Core.ConfigOperator import ConfigOperator

T = TypeVar('T')

# creates network properties that can be set by xtables
class PropertyOperator:
    __OPERATORS: Dict[str, 'PropertyOperator'] = {}

    def __init__(
        self,
        xclient: XTablesClient,
        configOp: ConfigOperator,
        logger: Logger,
        basePrefix: str = "",
        prefix: str = "",
    ) -> None:
        self.__xclient: XTablesClient = xclient
        self.__configOp: ConfigOperator = configOp
        self.Sentinel: Logger = logger
        self.basePrefix: str = basePrefix
        self.prefix: str = prefix

        self.__addBasePrefix: Callable[[str], str] = (
            lambda propertyTable: f"{self.basePrefix}.{propertyTable}"
        )
        self.__addFullPrefix: Callable[[str], str] = (
            lambda propertyTable: f"{self.basePrefix}{self.prefix}.{propertyTable}"
        )
        self.__getSaveFile: Callable[[], str] = lambda: self.__addFullPrefix("saved_properties.json")

        self.__propertyValueMap: Dict[str, Any] = self.__configOp.getContent(
            self.__getSaveFile(), default={}
        )
        self.__properties: Dict[str, 'Property'] = {}
        self.__readOnlyProperties: Dict[str, 'ReadonlyProperty'] = {}

        self.__getPropertyTable: Callable[[str], str] = lambda propertyName: self.__addFullPrefix(
            f"properties.EDITABLE.{propertyName}"
        )
        self.__getReadOnlyPropertyTable: Callable[[str], str] = lambda propertyName: self.__addFullPrefix(
            f"properties.READONLY.{propertyName}"
        )

        self.__children: List['PropertyOperator'] = []

    def getFullPrefix(self) -> str:
        return self.__addFullPrefix("")

    def __updatePropertyCallback(self, ret: Any) -> None:
        self.__propertyValueMap[ret.key] = self.__getRealType(ret.type, ret.value)
        # self.Sentinel.debug(f"Property updated | Name: {ret.key} Value : {ret.value}")

    def createProperty(
        self,
        propertyTable: str,
        propertyDefault,
        loadIfSaved=True,
        isCustom: bool = False,
        addBasePrefix: bool = True,
        addOperatorPrefix: bool = False,
        setDefaultOnNetwork: bool = True,
    ) -> "Property":
        """ Creates a network property that you can read from. To avoid conflicts, this property can only be read from, so its not writable.\n
            For a writable property, use whats called a '''ReadonlyProperty''' \n

            NOTE if you want to read from an existing table, and you are providing the absolute path in propertyTable, then mark isCustom True, and set the add...prefix arguments below it to False
            Args:
                propertyTable: str = The table name you wish to read from
                propertyDefault: Any = What default should it fallback to
                loadIfSaved: bool = Whether to make the property persistent or not
                isCustom: bool = Whether to use the custom add...prefix args  below
                addBasePrefix: bool = Whether to add the base hostname of the system
                addOperatorPrefix: bool = Whether to add whatever prefix this propertyOperator has. In an agent, this is the agent.getName()
                setDefaultOnNetwork: bool = Whether to push the default value you have onto the network.
          
          
        """
        if isCustom:
            if addBasePrefix and addOperatorPrefix:
                propertyTable = self.__addFullPrefix(propertyTable)
            elif addBasePrefix:
                propertyTable = self.__addBasePrefix(propertyTable)
        else:
            propertyTable = self.__getPropertyTable(
                propertyTable
            )  # store properties in known place

        # if this property already has been created, just give that one.
        if propertyTable in self.__properties:
            return self.__properties.get(propertyTable)

        # init default in map if not saved from previous run, or if you dont want to use a saved value
        if propertyTable not in self.__propertyValueMap or not loadIfSaved:
            if setDefaultOnNetwork:
                self.__setNetworkValue(propertyTable, propertyDefault)

            # if dosent exist, put default
            self.__propertyValueMap[propertyTable] = propertyDefault
            self.Sentinel.info(
                f"Created new property | Name: {propertyTable} Default: {propertyDefault} Type: {type(propertyDefault)}"
            )
        else:
            # exists, so put the value that it is onto network
            # NOTE: not checking to see if valid type, as for it to have been saved means it was already valid
            propertyValue = self.__propertyValueMap.get(propertyTable)
            if setDefaultOnNetwork:
                self.__setNetworkValue(propertyTable, propertyValue)

            self.Sentinel.info(
                f"Attached to saved property | Name: {propertyTable} Saved value: {propertyValue}"
            )

        # subscribe to any future updates
        self.__xclient.subscribe(propertyTable, self.__updatePropertyCallback)

        # getter function in a wrapper
        property = Property(
            lambda: self.__propertyValueMap[propertyTable], propertyTable=propertyTable
        )
        self.__properties[propertyTable] = property
        return property

    def createReadOnlyProperty(
        self, propertyName, propertyValue=None
    ) -> "ReadonlyProperty":
        propertyTable = self.__getReadOnlyPropertyTable(propertyName)
        return self.__createReadOnly(propertyTable, propertyValue)

    def createCustomReadOnlyProperty(
        self,
        propertyTable,
        propertyValue=None,
        addBasePrefix: bool = True,
        addOperatorPrefix: bool = False,
    ) -> "ReadonlyProperty":
        """Overrides any extra prefixes that might have been added by getting child property operators
        NOTE: by default addBasePrefix is True, and will add a base prefix to this property\n
        If you choose to remove the base prefix, be aware that separate devices/processes might write to the same tables

        """
        if addBasePrefix and addOperatorPrefix:
            propertyTable = self.__addFullPrefix(propertyTable)
        elif addBasePrefix:
            propertyTable = self.__addBasePrefix(propertyTable)

        return self.__createReadOnly(propertyTable, propertyValue)

    def __createReadOnly(self, propertyTable, propertyValue=None):
        if propertyTable in self.__readOnlyProperties:
            return self.__readOnlyProperties.get(propertyTable)

        if not self.__setNetworkValue(propertyTable, propertyValue, mute=True):
            self.Sentinel.debug(f"Initial network value cannot be set: {propertyValue}")

        readOnlyProp = ReadonlyProperty(
            lambda value: self.__setNetworkValue(propertyTable, value),
            propertyTable=propertyTable,
        )
        self.__readOnlyProperties[propertyTable] = readOnlyProp
        return readOnlyProp

    def __setNetworkValue(self, propertyTable, propertyValue, mute=False) -> bool:
        # send out default to network (assuming it initially does not exist. It shoudn't)
        if type(propertyValue) is str:
            self.__xclient.putString(propertyTable, propertyValue)
        elif type(propertyValue) is int:
            self.__xclient.putInteger(propertyTable, propertyValue)
        elif type(propertyValue) is float:
            self.__xclient.putDouble(propertyTable, propertyValue)
        elif type(propertyValue) is bytes:
            self.__xclient.putBytes(propertyTable, propertyValue)
        elif type(propertyValue) is bool:
            self.__xclient.putBoolean(propertyTable, propertyValue)
        elif type(propertyValue) is XTableValues.ProbabilityMappingDetections:
            # TODO: Figure out the NULL Proto error..
            # self.__xclient.putProbabilityMappingDetections(propertyTable, propertyValue)
            pass
        elif propertyValue is None:
            self.__xclient.putString(propertyTable, "NULLVALUE")
        elif type(propertyValue) is XTableValues.BezierCurves:
            self.__xclient.putBezierCurves(propertyTable, propertyValue)
        elif type(propertyValue) is Iterable:
            return self.__setNetworkIterable(propertyTable, propertyValue)
        else:
            if mute:
                self.Sentinel.error(f"Invalid property type!: {type(propertyValue)}")
            return False
        return True

    def __setNetworkIterable(self, propertyTable, propertyIterable: Iterable) -> bool:
        if propertyIterable is None:
            return False

        if not propertyIterable:
            # eg empty so can use any put method
            self.__xclient.putIntegerList(propertyTable, [])
            return True

        firstType = type(propertyIterable[0])

        putMethod = self.__getListTypeMethod(firstType)
        if not putMethod:
            self.Sentinel.debug(f"Invalid list type: {firstType}")
            return False

        for value in propertyIterable[1:]:
            if type(value) is not firstType:
                self.Sentinel.debug("List is not all same type!")
                return False

        putMethod(propertyTable, propertyIterable)
        return True

    def __getListTypeMethod(self, listType: type):
        if listType == float:
            return self.__xclient.putFloatList
        if listType == bytes:
            return self.__xclient.putBytesList
        if listType == bool:
            return self.__xclient.putBooleanList
        if listType == str:
            return self.__xclient.putStringList
        return None

    def __getRealType(self, type, propertyValue) -> bool:
        # get real type from xtable bytes
        if (
            type == XTableProto.XTableMessage.Type.UNKNOWN
            or type == XTableProto.XTableMessage.Type.BYTES
        ):
            return propertyValue
        elif type == XTableProto.XTableMessage.Type.INT64:
            return XTablesByteUtils.to_long(propertyValue)
        elif type == XTableProto.XTableMessage.Type.INT32:
            return XTablesByteUtils.to_int(propertyValue)
        elif type == XTableProto.XTableMessage.Type.DOUBLE:
            return XTablesByteUtils.to_double(propertyValue)
        elif type == XTableProto.XTableMessage.Type.BOOL:
            return XTablesByteUtils.to_boolean(propertyValue)
        elif type == XTableProto.XTableMessage.Type.STRING:
            return XTablesByteUtils.to_string(propertyValue)
        elif type == XTableProto.XTableMessage.Type.DOUBLE_LIST:
            return XTablesByteUtils.to_double_list(propertyValue)
        elif type == XTableValues.ProbabilityMappingDetections:
            return XTablesByteUtils.unpack_probability_mapping_detections(propertyValue)
        elif type == XTableProto.XTableMessage.Type.POSE2D:
            return XTablesByteUtils.unpack_pose2d(propertyValue)

        else:
            self.Sentinel.error(
                f"Invalid property type!: {XTableProto.XTableMessage.Type.Name(type)}"
            )
            return None

    def getChild(self, prefix: str) -> Optional["PropertyOperator"]:
        if not prefix:
            self.Sentinel.warning(
                "PropertyOperator getChild cannot take an empty string as a prefix!"
            )
            return None

        fullPrefix = f"{self.__getSaveFile()}.{prefix}"
        # see if a property operator with same prefixes has been created. To avoid issues you never want to create more than 1
        if fullPrefix in PropertyOperator.__OPERATORS:
            return PropertyOperator.__OPERATORS.get(fullPrefix)
        child = PropertyOperator(
            xclient=self.__xclient,
            logger=self.Sentinel,
            configOp=self.__configOp,
            basePrefix=self.basePrefix,
            prefix=f"{self.prefix}.{prefix}",
        )
        self.__children.append(child)
        # also add to Operators if someone in the future also wants to get the same child
        PropertyOperator.__OPERATORS[fullPrefix] = child
        return child

    def deregisterAll(self) -> bool:
        # unsubscribe from all callbacks
        wasAllRemoved = True
        for propertyTable in self.__propertyValueMap.keys():
            wasAllRemoved &= self.__xclient.unsubscribe(
                propertyTable, self.__updatePropertyCallback
            )

        # save property values
        self.__configOp.savePropertyToFileJSON(
            self.__getSaveFile(), self.__propertyValueMap
        )
        # now clear
        self.__propertyValueMap.clear()

        for child in self.__children:
            # "recursively" go through each child and deregister them too
            wasAllRemoved &= child.deregisterAll()
        return wasAllRemoved


class Property:
    def __init__(self, getFunc: Callable[[], T], propertyTable: str) -> None:  # lambda to get the property
        self.__getFunc: Callable[[], T] = getFunc
        self.__propertyTable: str = propertyTable

    def get(self) -> T:
        return self.__getFunc()

    def getTable(self) -> str:
        return self.__propertyTable


class ReadonlyProperty:
    def __init__(
        self, setFunc: Callable[[Any], bool], propertyTable: str
    ) -> None:  # lambda to set the read only property
        self.__setFunc: Callable[[Any], bool] = setFunc
        self.__propertyTable: str = propertyTable

    def set(self, value: Any) -> bool:
        return self.__setFunc(value)

    def getTable(self) -> str:
        return self.__propertyTable


class LambdaHandler(logging.Handler):
    def __init__(self, func: Callable[[str], None]) -> None:
        super().__init__()
        self.func: Callable[[str], None] = func  # This function will be executed on each log message

    def emit(self, record: logging.LogRecord) -> None:
        log_entry = self.format(record)  # Format log message
        self.func(log_entry)  # Call the lambda with the log entry
