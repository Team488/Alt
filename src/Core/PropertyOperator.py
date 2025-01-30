from logging import Logger
from JXTABLES.XTablesClient import XTablesClient
# creates network properties that can be set by xtables
class PropertyOperator:
    def __init__(self,xclient : XTablesClient, logger : Logger):
        self.Sentinel = logger
        self.__xclient : XTablesClient = xclient
        self.__propertyMap = {}
        self.__getPropertyTable = lambda propertyName : f"properties.{propertyName}"
        self.__getReadOnlyPropertyTable = lambda propertyName : f"properties.READONLY.{propertyName}"

    def __updatePropertyCallback(self,ret):
        self.__propertyMap[ret.key] = ret.value
        self.Sentinel.debug(f"Property updated | Name: {ret.key} Value : {ret.value}")

    def createProperty(self, propertyName : str, propertyDefault):
        propertyTable = self.__getPropertyTable(propertyName) # store properties in known place
        if not self.__setNetworkDefault(propertyTable,propertyDefault):
            return None
        
        # init default in map
        self.__propertyMap[propertyTable] = propertyDefault
        # subscribe to updates
        self.__xclient.subscribe(propertyTable,self.__updatePropertyCallback)
        self.Sentinel.info(f"Created property | Name: {propertyTable} Default: {propertyDefault} Type: {type(propertyDefault)}")
        return Property(lambda : self.__propertyMap[propertyTable])
    
    def createReadOnlyProperty(self, propertyName, propertyValue):
        propertyTable = self.__getReadOnlyPropertyTable(propertyName)
        self.__setNetworkDefault(propertyTable, propertyValue)
        
    def __setNetworkDefault(self, propertyTable, propertyDefault) -> bool:
        # send out default to network (assuming it initially does not exist. It shoudnt)
        if isinstance(propertyDefault,str):
            self.__xclient.putString(propertyTable,propertyDefault)
        elif isinstance(propertyDefault, int):
            self.__xclient.putInteger(propertyTable,propertyDefault)
        elif isinstance(propertyDefault, float):
            self.__xclient.putDouble(propertyTable,propertyDefault)
        elif isinstance(propertyDefault, list):
            self.__xclient.putArray(propertyTable,propertyDefault)
        elif isinstance(propertyDefault, bytes):
            self.__xclient.putBytes(propertyTable,propertyDefault)
        elif isinstance(propertyDefault, bool):
            self.__xclient.putBoolean(propertyTable,propertyDefault)
        else:
            self.Sentinel.error("Invalid property type!")
            return False

        return True
    
    def deregister(self):
        self.__xclient.unsubscribe_all(self.__updatePropertyCallback)


class Property:
    def __init__(self, getFunc): # lambda to get the property
        self.getFunc = getFunc
    
    def get(self):
        return self.getFunc()
    


