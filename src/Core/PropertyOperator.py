from logging import Logger
from JXTABLES.XTablesClient import XTablesClient
# creates network properties that can be set by xtables
class PropertyOperator:
    def __init__(self,xclient : XTablesClient, logger : Logger, prefix = ""):
        self.prefix = prefix
        self.Sentinel = logger
        self.__xclient : XTablesClient = xclient
        self.__propertyMap = {}
        self.__getPropertyTable = lambda propertyName : f"properties{self.prefix}.{propertyName}"
        self.__getReadOnlyPropertyTable = lambda propertyName : f"properties.READONLY{self.prefix}.{propertyName}"

    def __updatePropertyCallback(self,ret):
        self.__propertyMap[ret.key] = ret.value
        self.Sentinel.debug(f"Property updated | Name: {ret.key} Value : {ret.value}")

    def createProperty(self, propertyName : str, propertyDefault) -> "Property":
        propertyTable = self.__getPropertyTable(propertyName) # store properties in known place
        if not self.__setNetworkValue(propertyTable,propertyDefault):
            return None
        
        # init default in map
        self.__propertyMap[propertyTable] = propertyDefault
        # subscribe to updates
        self.__xclient.subscribe(propertyTable,self.__updatePropertyCallback)
        self.Sentinel.info(f"Created property | Name: {propertyTable} Default: {propertyDefault} Type: {type(propertyDefault)}")
        return Property(lambda : self.__propertyMap[propertyTable])
    
    def createReadOnlyProperty(self, propertyName, propertyValue) -> "ReadonlyProperty":
        propertyTable = self.__getReadOnlyPropertyTable(propertyName)
        if not self.__setNetworkValue(propertyTable, propertyValue):
            return None
        return ReadonlyProperty(lambda value : self.__setNetworkValue(propertyTable, value))


    def __setNetworkValue(self, propertyTable, propertyValue) -> bool:
        # send out default to network (assuming it initially does not exist. It shoudnt)
        if isinstance(propertyValue,str):
            self.__xclient.putString(propertyTable,propertyValue)
        elif isinstance(propertyValue, int):
            self.__xclient.putInteger(propertyTable,propertyValue)
        elif isinstance(propertyValue, float):
            self.__xclient.putDouble(propertyTable,propertyValue)
        elif isinstance(propertyValue, list):
            self.__xclient.putArray(propertyTable,propertyValue)
        elif isinstance(propertyValue, bytes):
            self.__xclient.putBytes(propertyTable,propertyValue)
        elif isinstance(propertyValue, bool):
            self.__xclient.putBoolean(propertyTable,propertyValue)
        else:
            self.Sentinel.error(f"Invalid property type!: {type(propertyValue)}")
            return False

        return True

    def getChild(self, prefix) -> "PropertyOperator":
        return PropertyOperator(self.__xclient, self.Sentinel, f"{self.prefix}.{prefix}")

    
    def deregister(self):
        self.__xclient.unsubscribe_all(self.__updatePropertyCallback)


class Property:
    def __init__(self, getFunc): # lambda to get the property
        self.getFunc = getFunc
    
    def get(self):
        return self.getFunc()
    
class ReadonlyProperty:
    def __init__(self, setFunc): # lambda to set the read only property
        self.setFunc = setFunc
    
    def set(self, value):
        return self.setFunc(value)
    


