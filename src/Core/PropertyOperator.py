import logging
from collections.abc import Iterable
from logging import Logger
from JXTABLES.XTablesClient import XTablesClient
from JXTABLES import XTableProto_pb2 as XTableProto
from JXTABLES.XTablesByteUtils import XTablesByteUtils
from Core.ConfigOperator import ConfigOperator

# creates network properties that can be set by xtables
class PropertyOperator:
    __OPERATORS = {}

    def __init__(
        self,
        xclient: XTablesClient,
        configOp: ConfigOperator,
        logger: Logger,
        basePrefix="",
        prefix="",
    ):
        self.__xclient: XTablesClient = xclient
        self.__configOp = configOp
        self.Sentinel = logger
        self.basePrefix = basePrefix
        self.prefix = prefix

        self.__addBasePrefix = (
            lambda propertyTable: f"{self.basePrefix}.{propertyTable}"
        )
        self.__addFullPrefix = (
            lambda propertyTable: f"{self.basePrefix}{self.prefix}.{propertyTable}"
        )
        self.__getSaveFile = lambda: self.__addFullPrefix("saved_properties.json")

        self.__propertyValueMap: dict = self.__configOp.getContent(
            self.__getSaveFile(), default={}
        )
        self.__properties = {}
        self.__readOnlyProperties = {}

        self.__getPropertyTable = lambda propertyName: self.__addFullPrefix(
            f"properties.EDITABLE.{propertyName}"
        )
        self.__getReadOnlyPropertyTable = lambda propertyName: self.__addFullPrefix(
            f"properties.READONLY.{propertyName}"
        )

        self.__children = []

    def __updatePropertyCallback(self, ret):
        self.__propertyValueMap[ret.key] = self.__getRealType(ret.type, ret.value)
        self.Sentinel.debug(f"Property updated | Name: {ret.key} Value : {ret.value}")

    def createProperty(self, propertyName: str, propertyDefault, loadIfSaved=True) -> "Property":
        propertyTable = self.__getPropertyTable(
            propertyName
        )  # store properties in known place

        # if this property already has been created, just give that one.
        if propertyTable in self.__properties:
            return self.__properties.get(propertyTable)

        # init default in map if not saved from previous run, or if you dont want to use a saved value
        if propertyTable not in self.__propertyValueMap or not loadIfSaved:
            # if its an invalid property type return immediately
            if not self.__setNetworkValue(propertyTable, propertyDefault):
                return None
            # if dosent exist, put default
            self.__propertyValueMap[propertyTable] = propertyDefault
            self.Sentinel.info(
                f"Created new property | Name: {propertyTable} Default: {propertyDefault} Type: {type(propertyDefault)}"
            )
        else:
            # exists, so put the value that it is onto network
            # NOTE: not checking to see if valid type, as for it to have been saved means it was already valid
            propertyValue = self.__propertyValueMap.get(propertyTable)
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

    def createReadOnlyProperty(self, propertyName, propertyValue) -> "ReadonlyProperty":
        propertyTable = self.__getReadOnlyPropertyTable(propertyName)
        return self.__createReadOnly(propertyTable, propertyValue)

    def createCustomReadOnlyProperty(
        self, propertyTable, propertyValue, addBasePrefix: bool = True
    ) -> "ReadonlyProperty":
        """Overrides any extra prefixes that might have been added by getting child property operators
        NOTE: by default addBasePrefix is True, and will add a base prefix to this property\n
        If you choose to remove the base prefix, be aware that separate devices/processes might write to the same tables

        """
        if addBasePrefix:
            propertyTable = self.__addBasePrefix(propertyTable)
        return self.__createReadOnly(propertyTable, propertyValue)

    def __createReadOnly(self, propertyTable, propertyValue):
        if propertyTable in self.__readOnlyProperties:
            return self.__readOnlyProperties.get(propertyTable)
        if not self.__setNetworkValue(propertyTable, propertyValue):
            return None

        readOnlyProp = ReadonlyProperty(
            lambda value: self.__setNetworkValue(propertyTable, value),
            propertyTable=propertyTable,
        )
        self.__readOnlyProperties[propertyTable] = readOnlyProp
        return readOnlyProp

    def __setNetworkValue(self, propertyTable, propertyValue) -> bool:
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
        elif type(propertyValue) is Iterable:
            return self.__setNetworkIterable(propertyTable, propertyValue)
        else:
            self.Sentinel.error(f"Invalid property type!: {type(propertyValue)}")
            return False
        return True

    def __setNetworkIterable(self, propertyTable, propertyIterable: Iterable):
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
        elif type == XTableProto.XTableMessage.Type.DOUBLE:
            return XTablesByteUtils.to_double(propertyValue)
        elif type == XTableProto.XTableMessage.Type.BOOL:
            return XTablesByteUtils.to_boolean(propertyValue)
        elif type == XTableProto.XTableMessage.Type.STRING:
            return XTablesByteUtils.to_string(propertyValue)

        # TODO add list methods here -----------------

        else:
            self.Sentinel.error(f"Invalid property type!: {type(propertyValue)}")
            return None

    def getChild(self, prefix) -> "PropertyOperator":
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

    def deregisterAll(self):
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
    def __init__(self, getFunc, propertyTable):  # lambda to get the property
        self.__getFunc = getFunc
        self.__propertyTable = propertyTable

    def get(self):
        return self.__getFunc()

    def getTable(self):
        return self.__propertyTable


class ReadonlyProperty:
    def __init__(self, setFunc, propertyTable):  # lambda to set the read only property
        self.__setFunc = setFunc
        self.__propertyTable = propertyTable

    def set(self, value):
        return self.__setFunc(value)

    def getTable(self):
        return self.__propertyTable


class LambdaHandler(logging.Handler):
    def __init__(self, func):
        super().__init__()
        self.func = func  # This function will be executed on each log message

    def emit(self, record):
        log_entry = self.format(record)  # Format log message
        self.func(log_entry)  # Call the lambda with the log entry
