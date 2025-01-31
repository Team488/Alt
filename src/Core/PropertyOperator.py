import os
from logging import Logger
from JXTABLES.XTablesClient import XTablesClient
from JXTABLES import XTableProto_pb2 as XTableProto
from JXTABLES.XTablesByteUtils import XTablesByteUtils
from Core.ConfigOperator import ConfigOperator

# creates network properties that can be set by xtables
class PropertyOperator:
    __OPERATORS = {}
    def __init__(self, xclient: XTablesClient, configOp : ConfigOperator, logger: Logger, basePrefix = "", prefix=""):
        self.__xclient: XTablesClient = xclient
        self.__configOp = configOp
        self.Sentinel = logger
        self.basePrefix = basePrefix
        self.prefix = prefix

        self.__addBasePrefix = (
            lambda propertyTable: f"{self.basePrefix}{self.prefix}.{propertyTable}"
        )
        self.__getSaveFile = (
            lambda : self.__addBasePrefix('saved_properties.json')
        )

        self.__propertyValueMap : dict = self.__configOp.getContent(self.__getSaveFile(), default={})
        self.__properties = {}
        self.__readOnlyProperties = {}
        
        self.__getPropertyTable = (
            lambda propertyName: self.__addBasePrefix(f"properties.EDITABLE.{propertyName}")
        )
        self.__getReadOnlyPropertyTable = (
            lambda propertyName: self.__addBasePrefix(f"properties.READONLY.{propertyName}")
        )
        
        self.__children = []

    def __updatePropertyCallback(self, ret):
        self.__propertyValueMap[ret.key] = self.__getRealType(ret.type, ret.value)
        self.Sentinel.debug(f"Property updated | Name: {ret.key} Value : {ret.value}")

    def createProperty(self, propertyName: str, propertyDefault) -> "Property":
        propertyTable = self.__getPropertyTable(
            propertyName
        )  # store properties in known place

        # if this property already has been created, just give that one.
        if propertyTable in self.__properties:
            return self.__properties.get(propertyTable)
        
        # init default in map if not saved from previous run
        if propertyTable not in self.__propertyValueMap:
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
        property = Property(lambda: self.__propertyValueMap[propertyTable])
        self.__properties[propertyTable] = property
        return property

    def createReadOnlyProperty(self, propertyName, propertyValue) -> "ReadonlyProperty":
        propertyTable = self.__getReadOnlyPropertyTable(propertyName)
        return self.__createReadOnly(propertyTable, propertyValue)

    def createCustomReadOnlyProperty(
        self, propertyTable, propertyValue
    ) -> "ReadonlyProperty":
        prefixed = self.__addBasePrefix(propertyTable)
        return self.__createReadOnly(prefixed, propertyValue)

    def __createReadOnly(self, propertyTable, propertyValue):
        if propertyTable in self.__readOnlyProperties:
            return self.__readOnlyProperties.get(propertyTable)
        if not self.__setNetworkValue(propertyTable, propertyValue):
            return None

        readOnlyProp = ReadonlyProperty(
            lambda value: self.__setNetworkValue(propertyTable, value)
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
        else:
            self.Sentinel.error(f"Invalid property type!: {type(propertyValue)}")
            return False
        return True

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
        else:
            self.Sentinel.error(f"Invalid property type!: {type(propertyValue)}")
            return None
    
    def getChild(self, prefix) -> "PropertyOperator":
        if not prefix:
            self.Sentinel.warning("PropertyOperator getChild cannot take an empty string as a prefix!")
            return None
        
        fullPrefix = f"{self.__getSaveFile()}.{prefix}"
        # see if a property operator with same prefixes has been created. To avoid issues you never want to create more than 1
        if fullPrefix in PropertyOperator.__OPERATORS:
            return PropertyOperator.__OPERATORS.get(fullPrefix)
        child = PropertyOperator(
            xclient=self.__xclient, logger=self.Sentinel, configOp=self.__configOp, basePrefix=self.basePrefix, prefix=f"{self.prefix}.{prefix}"
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
        self.__configOp.savePropertyToFileJSON(self.__getSaveFile(),self.__propertyValueMap)
        # now clear
        self.__propertyValueMap.clear()

        for child in self.__children:
            # "recursively" go through each child and deregister them too
            wasAllRemoved &= child.deregisterAll()
        return wasAllRemoved


class Property:
    def __init__(self, getFunc):  # lambda to get the property
        self.getFunc = getFunc

    def get(self):
        return self.getFunc()


class ReadonlyProperty:
    def __init__(self, setFunc):  # lambda to set the read only property
        self.setFunc = setFunc

    def set(self, value):
        return self.setFunc(value)
