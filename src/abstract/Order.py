"""
Order Module - Base class for all one-time executable commands.

An Order (also known as a command) represents a discrete task that is triggered
once and then executed. Orders follow a simple lifecycle:
1. Creation - Initial setup (create method)
2. Execution - Perform the task (run method)
3. Cleanup - Release resources (cleanup method)

Orders are used for one-time operations or responses to external events.
Unlike Agents, which run continuously, Orders execute once and then terminate.

Notes:
    - Orders receive shared system objects via the inject method
    - Order-specific objects should be created in the create method
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

from JXTABLES.XTablesClient import XTablesClient
from Core.Central import Central
from Core.PropertyOperator import PropertyOperator
from Core.ConfigOperator import ConfigOperator
from Core.ShareOperator import ShareOperator
from Core.TimeOperator import Timer


class Order(ABC):
    """
    Abstract base class for all order implementations.
    
    Orders are one-time executable commands that perform a discrete task
    and then terminate. They provide a way to encapsulate specific operations
    that need to be triggered in response to events or user actions.
    
    Attributes:
        central (Optional[Central]): Reference to central coordination system
        xclient (Optional[XTablesClient]): Network tables client for communication
        propertyOperator (Optional[PropertyOperator]): Access to system properties
        configOperator (Optional[ConfigOperator]): Access to configuration values
        shareOperator (Optional[ShareOperator]): Manages shared objects between components
        timer (Optional[Timer]): Timing utility for performance monitoring
    """
    def __init__(self) -> None:
        """
        Initialize the order with default values.
        
        The constructor only initializes member variables to their default values.
        No actual setup should happen here - use the create() method instead.
        """
        self.central: Optional[Central] = None
        self.xclient: Optional[XTablesClient] = None
        self.propertyOperator: Optional[PropertyOperator] = None
        self.configOperator: Optional[ConfigOperator] = None
        self.shareOperator: Optional[ShareOperator] = None
        self.timer: Optional[Timer] = None

    def inject(
        self,
        central: Central,
        xclient: XTablesClient,
        propertyOperator: PropertyOperator,
        configOperator: ConfigOperator,
        shareOperator: ShareOperator,
        timer: Timer,
    ) -> None:
        """
        Inject required system components into the order.
        
        This method is called by the OrderOperator to provide the order with
        access to system-wide shared resources. Subclasses should not override
        this method.
        
        Args:
            central: Central coordination system instance
            xclient: XTables client for network communication
            propertyOperator: Access to system properties
            configOperator: Access to configuration values
            shareOperator: For sharing objects between components
            timer: Timing utility for performance monitoring
        """
        self.central = central
        self.xclient = xclient
        self.propertyOperator = propertyOperator
        self.configOperator = configOperator
        self.shareOperator = shareOperator
        self.timer = timer

    def getTimer(self) -> Timer:
        """
        Get the timer instance associated with this order.
        
        Returns:
            Timer: The timer instance for performance monitoring
            
        Raises:
            ValueError: If the timer has not been initialized
            
        Note:
            Use only when needed, and only for operations associated with this order.
        """
        if self.timer is None:
            raise ValueError("Timer not initialized")
        return self.timer

    @abstractmethod
    def create(self) -> None:
        """
        Perform one-time initialization of the order.
        
        This method is called once when the order is first created, before
        the run method is called. Use it to initialize resources, open connections,
        or perform any other setup needed for the order to execute.
        
        Note:
            This will not be called multiple times, even if the order is run
            multiple times. For operations that should happen before each run,
            put them at the beginning of the run method.
        """
        pass

    @abstractmethod
    def run(self, input: Any) -> Any:
        """
        Execute the order's main functionality.
        
        This method is called once per order execution and should contain the
        main logic for the order.
        
        Args:
            input: Input data passed to the order by the caller
            
        Returns:
            Any: Result of the order execution, to be returned to the caller
        """
        pass

    @abstractmethod
    def getDescription(self) -> str:
        """
        Get a description of the order's purpose.
        
        Returns:
            str: A concise description of what the order does
        """
        pass

    def getName(self) -> str:
        """
        Get the name of the order.
        
        The default implementation returns the class name. Subclasses can
        override this to provide a custom name.
        
        Returns:
            str: The name of the order
        """
        return self.__class__.__name__

    def cleanup(self) -> None:
        """
        Perform cleanup tasks when the order completes.
        
        This method is called after the run method completes, regardless of
        whether it was successful or raised an exception. Use it to release
        resources, close connections, or perform any other cleanup needed.
        
        The default implementation does nothing. Override this method to
        implement custom cleanup logic.
        """
        pass
