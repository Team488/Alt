import logging
from JXTABLES.XTablesClient import XTablesClient
Sentinel = logging.getLogger("Property_Operator")
# creates network properties that can be set by xtables
class PropertyOperator:
    def __init__(self,xclient : XTablesClient):
        self.__xclient : XTablesClient = xclient
        self.__propertyMap = {}

    def __updatePropertyCallback(self,ret):
        self.__propertyMap[ret.key] = ret.value
        Sentinel.debug(f"Property updated | Name: {ret.key} Value : {ret.value}")

    def createProperty(self, propertyName : str, propertyDefault):
        if not self.__setNetworkDefault(propertyName,propertyDefault):
            return None
        
        # init default in map
        self.__propertyMap[propertyName] = propertyDefault
        # subscribe to updates
        self.__xclient.subscribe(propertyName,self.__updatePropertyCallback)
        Sentinel.info(f"Created property | Name: {propertyName} Default: {propertyDefault} Type {type(propertyDefault)}")
        return Property(lambda : self.__propertyMap[propertyName])
        
    def __setNetworkDefault(self, propertyName, propertyDefault) -> bool:
        # send out default to network (assuming it initially does not exist. It shoudnt)
        if isinstance(propertyDefault,str):
            self.__xclient.putString(propertyName,propertyDefault)
        elif isinstance(propertyDefault, int):
            self.__xclient.putInteger(propertyName,propertyDefault)
        elif isinstance(propertyDefault, float):
            self.__xclient.putDouble(propertyName,propertyDefault)
        elif isinstance(propertyDefault, list):
            self.__xclient.putArray(propertyName,propertyDefault)
        elif isinstance(propertyDefault, bytes):
            self.__xclient.putBytes(propertyName,propertyDefault)
        elif isinstance(propertyDefault, bool):
            self.__xclient.putBoolean(propertyName,propertyDefault)
        else:
            Sentinel.error("Invalid property type!")
            return False

        return True
    
    def deregister(self):
        self.__xclient.unsubscribe_all(self.__updatePropertyCallback)


class Property:
    def __init__(self, getFunc): # lambda to get the property
        self.getFunc = getFunc
    
    def get(self):
        return self.getFunc()
    


