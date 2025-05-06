"""PropertyOperator.py

Provides the PropertyOperator class and related classes for managing network properties,
including editable and read-only properties, and their integration with XTables.

Classes:
    PropertyOperator: Manages network properties for agents, including creation, updates, and persistence.
    Property: Represents a readable property.
    ReadonlyProperty: Represents a writable (read-only from the network) property.
    LambdaHandler: Logging handler that executes a lambda on each log message.
"""

import logging
from typing import Sequence
from typing import Dict, List, Any, Optional, Callable
from JXTABLES.XTablesClient import XTablesClient
from JXTABLES import XTableProto_pb2 as XTableProto
from JXTABLES import XTableValues_pb2 as XTableValues
from JXTABLES.XTablesByteUtils import XTablesByteUtils
from .ConfigOperator import ConfigOperator
from .LogOperator import getChildLogger

Sentinel = getChildLogger("Property_Operator")

class PropertyOperator:
    """
    Creates and manages network properties that can be set and read by XTables.

    Handles both editable and read-only properties, supports property persistence,
    and provides methods for property injection and deregistration.
    """

    __OPERATORS: Dict[str, "PropertyOperator"] = {}

    def __init__(
        self,
        xclient: XTablesClient,
        configOp: ConfigOperator,
        prefix: str = "",
    ) -> None:
        """
        Initializes a PropertyOperator.

        Args:
            xclient (XTablesClient): The XTables client instance.
            configOp (ConfigOperator): The configuration operator.
            prefix (str, optional): Prefix for property names.
        """
        from .. import DEVICEHOSTNAME

        self.__xclient: XTablesClient = xclient
        self.__configOp: ConfigOperator = configOp
        self.basePrefix: str = DEVICEHOSTNAME
        if not prefix.startswith("."):
            self.prefix: str = f".{prefix}"
        else:
            self.prefix = prefix

        self.__addBasePrefix: Callable[
            [str], str
        ] = lambda propertyTable: f"{self.basePrefix}.{propertyTable}"
        self.__addFullPrefix: Callable[
            [str], str
        ] = lambda propertyTable: f"{self.basePrefix}{self.prefix}.{propertyTable}"
        self.__getSaveFile: Callable[[], str] = lambda: self.__addFullPrefix(
            "saved_properties.json"
        )

        self.__propertyValueMap: Dict[str, Any] = self.__configOp.getContent(
            self.__getSaveFile(), default={}
        )
        self.__properties: Dict[str, "Property"] = {}
        self.__readOnlyProperties: Dict[str, "ReadonlyProperty"] = {}

        self.__getPropertyTable: Callable[
            [str], str
        ] = lambda propertyName: self.__addFullPrefix(
            f"properties.EDITABLE.{propertyName}"
        )
        self.__getReadOnlyPropertyTable: Callable[
            [str], str
        ] = lambda propertyName: self.__addFullPrefix(
            f"properties.READONLY.{propertyName}"
        )

        self.__children: List["PropertyOperator"] = []

    def getFullPrefix(self) -> str:
        """
        Returns the full prefix for this property operator.

        Returns:
            str: The full prefix.
        """
        return self.__addFullPrefix("")[:-1]  # remove trailing dot

    def __updatePropertyCallback(self, ret: Any) -> None:
        """
        Callback for property updates from XTables.

        Args:
            ret (Any): The update result object.
        """
        self.__propertyValueMap[ret.key] = self.__getRealValue(ret.type, ret.value)
        # Sentinel.debug(f"Property updated | Name: {ret.key} Value : {ret.value}")

    def createReadExistingNetworkValueProperty(
        self, propertyTable: str, propertyDefault: Any = None
    ):
        """
        Use to get a property that reads from an existing table on XTables.

        Args:
            propertyTable (str): The table name to read from.
            propertyDefault (Any, optional): Default value if not found.

        Returns:
            Property: The created property.
        """
        return self._createProperty(
            propertyTable,
            propertyDefault,
            loadIfSaved=False,
            isCustom=True,
            addBasePrefix=False,
            addOperatorPrefix=False,
            setDefaultOnNetwork=False,
        )
    
    def createCustomProperty(
        self,
        propertyTable: str,
        propertyDefault: Any,
        loadIfSaved: bool = True,
        addBasePrefix: bool = True,
        addOperatorPrefix: bool = True,
        setDefaultOnNetwork: bool = True,   
    ) -> "Property":
        """
        Create a custom property with configurable prefix and persistence.

        Args:
            propertyTable (str): The table name.
            propertyDefault (Any): Default value.
            loadIfSaved (bool): Whether to load saved value.
            addBasePrefix (bool): Whether to add the base prefix.
            addOperatorPrefix (bool): Whether to add the operator prefix.
            setDefaultOnNetwork (bool): Whether to push the default value to the network.

        Returns:
            Property: The created property.
        """
        return self._createProperty(propertyTable, propertyDefault, loadIfSaved, True, addBasePrefix, addOperatorPrefix, setDefaultOnNetwork)
    
    def createProperty(
        self,
        propertyTable: str,
        propertyDefault: Any,
        loadIfSaved: bool = True,
        setDefaultOnNetwork: bool = True,
    ):
        """
        Create a standard property with default prefixing and persistence.

        Args:
            propertyTable (str): The table name.
            propertyDefault (Any): Default value.
            loadIfSaved (bool): Whether to load saved value.
            setDefaultOnNetwork (bool): Whether to push the default value to the network.

        Returns:
            Property: The created property.
        """
        return self._createProperty(propertyTable, propertyDefault, loadIfSaved, False, True, True, setDefaultOnNetwork)

    def _createProperty(
        self,
        propertyTable: str,
        propertyDefault,
        loadIfSaved: bool,
        isCustom: bool,
        addBasePrefix: bool,
        addOperatorPrefix: bool,
        setDefaultOnNetwork: bool,
    ) -> "Property":
        """
        Creates a network property that you can read from. To avoid conflicts, this property can only be read from, so its not writable.
        For a writable property, use a ReadonlyProperty.

        Args:
            propertyTable (str): The table name you wish to read from.
            propertyDefault (Any): What default should it fallback to.
            loadIfSaved (bool): Whether to make the property persistent or not.
            isCustom (bool): Whether to use the custom add...prefix args below.
            addBasePrefix (bool): Whether to add the base hostname of the system.
            addOperatorPrefix (bool): Whether to add whatever prefix this propertyOperator has.
            setDefaultOnNetwork (bool): Whether to push the default value you have onto the network.

        Returns:
            Property: The created property.
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
            return self.__properties[propertyTable]

        # init default in map if not saved from previous run, or if you dont want to use a saved value
        if propertyTable not in self.__propertyValueMap or not loadIfSaved:
            if setDefaultOnNetwork:
                self.__setNetworkValue(propertyTable, propertyDefault)

            # if dosent exist, put default
            self.__propertyValueMap[propertyTable] = propertyDefault
            Sentinel.info(
                f"Created new property | Name: {propertyTable} Default: {propertyDefault} Type: {type(propertyDefault)}"
            )
        else:
            # exists, so put the value that it is onto network
            # NOTE: not checking to see if valid type, as for it to have been saved means it was already valid
            propertyValue = self.__propertyValueMap.get(propertyTable)
            if setDefaultOnNetwork:
                self.__setNetworkValue(propertyTable, propertyValue)

            Sentinel.info(
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
        """
        Create a read-only property with the given name and value.

        Args:
            propertyName (str): The property name.
            propertyValue (Any, optional): The value to set.

        Returns:
            ReadonlyProperty: The created read-only property.
        """
        propertyTable = self.__getReadOnlyPropertyTable(propertyName)
        return self.__createReadOnly(propertyTable, propertyValue)
    
    def setPropertyTable(
        self,
        propertyTable,
        propertyValue=None,
    ):
        """
        Set a property table to a specific value.

        Args:
            propertyTable (str): The property table name.
            propertyValue (Any, optional): The value to set.
        """
        self.createCustomReadOnlyProperty(propertyTable, propertyValue, False, False).set(propertyValue)

    def createCustomReadOnlyProperty(
        self,
        propertyTable,
        propertyValue=None,
        addBasePrefix: bool = True,
        addOperatorPrefix: bool = False,
    ) -> "ReadonlyProperty":
        """
        Overrides any extra prefixes that might have been added by getting child property operators.
        NOTE: by default addBasePrefix is True, and will add a base prefix to this property.
        If you choose to remove the base prefix, be aware that separate devices/processes might write to the same tables

        Args:
            propertyTable (str): The property table name.
            propertyValue (Any, optional): The value to set.
            addBasePrefix (bool): Whether to add the base prefix.
            addOperatorPrefix (bool): Whether to add the operator prefix.

        Returns:
            ReadonlyProperty: The created read-only property.
        """
        if addBasePrefix and addOperatorPrefix:
            propertyTable = self.__addFullPrefix(propertyTable)
        elif addBasePrefix:
            propertyTable = self.__addBasePrefix(propertyTable)

        return self.__createReadOnly(propertyTable, propertyValue)

    def __createReadOnly(self, propertyTable, propertyValue=None):
        """
        Internal method to create a read-only property.

        Args:
            propertyTable (str): The property table name.
            propertyValue (Any, optional): The value to set.

        Returns:
            ReadonlyProperty: The created read-only property.
        """
        if propertyTable in self.__readOnlyProperties:
            return self.__readOnlyProperties.get(propertyTable)

        if not self.__setNetworkValue(propertyTable, propertyValue, mute=True):
            Sentinel.debug(f"Initial network value cannot be set: {propertyValue}")

        readOnlyProp = ReadonlyProperty(
            lambda value: self.__setNetworkValue(propertyTable, value),
            propertyTable=propertyTable,
        )
        self.__readOnlyProperties[propertyTable] = readOnlyProp
        return readOnlyProp

    def __setNetworkValue(self, propertyTable, propertyValue, mute=False) -> bool:
        """
        Set a value on the network for a property table.

        Args:
            propertyTable (str): The property table name.
            propertyValue (Any): The value to set.
            mute (bool): If True, suppress error logging.

        Returns:
            bool: True if the value was set successfully, False otherwise.
        """
        # send out default to network (could and would overwrite any existing thing in the propertyTable)
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
        elif isinstance(propertyValue, Sequence):
            return self.__setNetworkIterable(propertyTable, propertyValue)
        else:
            if not mute:
                Sentinel.error(f"Invalid property type!: {type(propertyValue)}")
            return False
        return True

    def __setNetworkIterable(self, propertyTable, propertyIterable: Sequence) -> bool:
        """
        Set a sequence value on the network for a property table.

        Args:
            propertyTable (str): The property table name.
            propertyIterable (Sequence): The sequence to set.

        Returns:
            bool: True if the sequence was set successfully, False otherwise.
        """
        if propertyIterable is None:
            return False

        if not propertyIterable:
            # NEEDS FIX, need to know empty list type 
            self.__xclient.putStringList(propertyTable, [])
            return True

        firstType = type(propertyIterable[0])

        putMethod = self.__getListTypeMethod(firstType)
        if not putMethod:
            Sentinel.debug(f"Invalid list type: {firstType}")
            return False

        for value in propertyIterable[1:]:
            if type(value) is not firstType:
                Sentinel.debug("List is not all same type!")
                return False

        putMethod(propertyTable, propertyIterable)
        return True

    def __getListTypeMethod(self, listType: type):
        """
        Get the appropriate XTables put method for a list type.

        Args:
            listType (type): The type of the list elements.

        Returns:
            callable or None: The put method, or None if not found.
        """
        if listType == float:
            return self.__xclient.putFloatList
        if listType == bytes:
            return self.__xclient.putBytesList
        if listType == bool:
            return self.__xclient.putBooleanList
        if listType == str:
            return self.__xclient.putStringList
        return None

    def __getRealValue(self, type, propertyValue) -> Any:
        """
        Convert a network value to its real Python type.

        Args:
            type: The type identifier from XTables.
            propertyValue: The value to convert.

        Returns:
            Any: The converted value.
        """
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
        elif type == XTableProto.XTableMessage.Type.STRING_LIST:
            return XTablesByteUtils.to_string_list(propertyValue)
        elif type == XTableProto.XTableMessage.Type.INTEGER_LIST:
            return XTablesByteUtils.to_integer_list(propertyValue)

        else:
            Sentinel.error(
                f"Invalid property type!: {XTableProto.XTableMessage.Type.Name(type)}"
            )
            return None

    def getChild(self, prefix: str) -> Optional["PropertyOperator"]:
        """
        Get a child PropertyOperator with an additional prefix.

        Args:
            prefix (str): The prefix for the child operator.

        Returns:
            Optional[PropertyOperator]: The child PropertyOperator, or None if not found.
        """
        if not prefix:
            raise ValueError(
                "PropertyOperator getChild must have a nonempty prefix!"
            )

        fullPrefix = f"{self.__getSaveFile()}.{prefix}"
        # see if a property operator with same prefixes has been created. To avoid issues you never want to create more than 1
        if fullPrefix in PropertyOperator.__OPERATORS:
            return PropertyOperator.__OPERATORS.get(fullPrefix)
        child = PropertyOperator(
            xclient=self.__xclient,
            configOp=self.__configOp,
            prefix=f"{self.prefix}.{prefix}",
        )
        self.__children.append(child)
        # also add to Operators if someone in the future also wants to get the same child
        PropertyOperator.__OPERATORS[fullPrefix] = child
        return child

    def deregisterAll(self) -> bool:
        """
        Unsubscribe from all property callbacks and clear property values.

        Returns:
            bool: True if all were removed, False otherwise.
        """
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
    """
    Represents a readable property.

    Args:
        getFunc (Callable[[], Any]): Function to get the property value.
        propertyTable (str): The property table name.
    """

    def __init__(
        self, getFunc: Callable[[], Any], propertyTable: str
    ) -> None:
        self.__getFunc: Callable[[], Any] = getFunc
        self.__propertyTable: str = propertyTable

    def get(self) -> Any:
        """
        Get the value of the property.

        Returns:
            Any: The property value.
        """
        return self.__getFunc()

    def getTable(self) -> str:
        """
        Get the property table name.

        Returns:
            str: The property table name.
        """
        return self.__propertyTable


class ReadonlyProperty:
    """
    Represents a writable (read-only from the network) property.

    Args:
        setFunc (Callable[[Any], bool]): Function to set the property value.
        propertyTable (str): The property table name.
    """

    def __init__(
        self, setFunc: Callable[[Any], bool], propertyTable: str
    ) -> None:
        self.__setFunc: Callable[[Any], bool] = setFunc
        self.__propertyTable: str = propertyTable

    def set(self, value: Any) -> bool:
        """
        Set the value of the property.

        Args:
            value (Any): The value to set.

        Returns:
            bool: True if set successfully, False otherwise.
        """
        return self.__setFunc(value)

    def getTable(self) -> str:
        """
        Get the property table name.

        Returns:
            str: The property table name.
        """
        return self.__propertyTable


class LambdaHandler(logging.Handler):
    """
    Logging handler that executes a lambda function on each log message.

    Args:
        func (Callable[[str], None]): The function to execute on each log message.
    """

    def __init__(self, func: Callable[[str], None]) -> None:
        super().__init__()
        self.func: Callable[
            [str], None
        ] = func  # This function will be executed on each log message

    def emit(self, record: logging.LogRecord) -> None:
        """
        Emit a log record and execute the lambda function.

        Args:
            record (logging.LogRecord): The log record to emit.
        """
        log_entry = self.format(record)  # Format log message
        self.func(log_entry)  # Call the lambda with the log entry
