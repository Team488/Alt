"""
Agent Module - Base class for all long-running agents in the system.

Agents (also known as tasks) are long-running processes with a defined lifecycle:
1. Creation - Initial setup (create method)
2. Running - Continuous operation until shutdown/task completion (runPeriodic method)
3. Optional shutdown - Handle force shutdown requests (forceShutdown method)
4. Cleanup - Release resources and perform final actions (onClose method)

Most agents run for the duration of the system's operation.

Notes:
    - Agents receive shared objects via the inject method
    - Agent-specific objects should be created in the create method
"""

from abc import ABC, abstractmethod
from logging import Logger
from typing import Optional, Any

from JXTABLES.XTablesClient import XTablesClient
from Core.UpdateOperator import UpdateOperator
from Core.Central import Central
from Core.PropertyOperator import PropertyOperator
from Core.ConfigOperator import ConfigOperator
from Core.ShareOperator import ShareOperator
from Core.TimeOperator import Timer
from tools.Constants import TEAM


class Agent(ABC):
    """
    Abstract base class for all agent implementations.
    
    Agents perform various tasks in the system, such as processing camera feeds,
    tracking objects, planning paths, or controlling peripherals.
    
    Attributes:
        DEFAULT_LOOP_TIME (int): Default loop interval in milliseconds (0 = no delay)
        hasShutdown (bool): Flag indicating if the agent has been shut down
        hasClosed (bool): Flag indicating if the agent has been closed
        central (Optional[Central]): Reference to central coordination system
        xclient (Optional[XTablesClient]): Network tables client for communication
        propertyOperator (Optional[PropertyOperator]): Access to system properties
        configOperator (Optional[ConfigOperator]): Access to configuration values
        shareOp (Optional[ShareOperator]): Manages shared objects between agents
        updateOp (Optional[UpdateOperator]): Handles update operations
        Sentinel (Optional[Logger]): Logging facility
        timer (Optional[Timer]): Timing utility for performance monitoring
        isMainThread (bool): Flag indicating if agent runs on main thread
    """
    DEFAULT_LOOP_TIME: int = 0  # 0 ms

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize the agent with default values.
        
        Args:
            **kwargs: Arbitrary keyword arguments (not used in base implementation)
        
        Note:
            This constructor only initializes variables to default values.
            No actual setup should happen here - use the create() method instead.
        """
        # nothing should go here
        self.hasShutdown: bool = False
        self.hasClosed: bool = False
        self.central: Optional[Central] = None
        self.xclient: Optional[XTablesClient] = None
        self.propertyOperator: Optional[PropertyOperator] = None
        self.configOperator: Optional[ConfigOperator] = None
        self.shareOp: Optional[ShareOperator] = None
        self.updateOp: Optional[UpdateOperator] = None
        self.Sentinel: Optional[Logger] = None
        self.timer: Optional[Timer] = None
        self.isMainThread: bool = False

    def inject(
        self,
        central: Central,
        xclient: XTablesClient,
        propertyOperator: PropertyOperator,
        configOperator: ConfigOperator,
        shareOperator: ShareOperator,
        updateOperator: UpdateOperator,
        logger: Logger,
        timer: Timer,
        isMainThread: bool,
    ) -> None:
        """
        Injects required system components into the agent.
        
        This method is called by the AgentOperator to provide the agent with
        access to system-wide shared resources. Subclasses should not override this method.
        
        Args:
            central: Central coordination system instance
            xclient: XTables client for network communication
            propertyOperator: Access to system properties
            configOperator: Access to configuration values
            shareOperator: For sharing objects between agents
            updateOperator: Manages update operations
            logger: Logging facility
            timer: Timing utility for performance monitoring
            isMainThread: Flag indicating if agent runs on main thread
        """
        self.central = central
        self.xclient = xclient
        self.propertyOperator = propertyOperator
        self.configOperator = configOperator
        self.shareOp = shareOperator
        self.updateOp = updateOperator
        self.Sentinel = logger
        self.timer = timer
        self.isMainThread = isMainThread
        # other than setting variables, nothing should go here

    def getTimer(self) -> Timer:
        """
        Get the timer instance associated with this agent.
        
        Returns:
            Timer: The timer instance for performance monitoring
            
        Raises:
            ValueError: If the timer has not been initialized
            
        Note:
            Use only when needed, and only when associated with agent.
        """
        if self.timer is None:
            raise ValueError("Timer not initialized")
        return self.timer

    def getTeam(self) -> Optional[TEAM]:
        """
        Fetch the current team color from XTables.
        
        Returns:
            Optional[TEAM]: TEAM.BLUE, TEAM.RED, or None if not set
            
        Raises:
            ValueError: If the XTablesClient has not been initialized
            
        Note:
            This value may not be reliable during system initialization.
        """
        if self.xclient is None:
            raise ValueError("XTablesClient not initialized")
            
        team: Optional[str] = self.xclient.getString("TEAM")
        if team is None:
            return None

        if team.lower() == "blue":
            return TEAM.BLUE
        else:
            return TEAM.RED

    # ----- Required Implementations -----

    @abstractmethod
    def create(self) -> None:
        """
        Initialize the agent.
        
        This method is called once when the agent is first created. Perform 
        all initialization tasks here, such as opening cameras, initializing
        resources, or setting up data structures. This is preferred over putting
        initialization in the constructor.
        
        Returns:
            None
        """
        pass

    @abstractmethod
    def runPeriodic(self) -> None:
        """
        Execute the agent's main function periodically.
        
        This method is called repeatedly in a loop until isRunning() returns False
        or the agent is forcibly shut down. Each invocation should perform a single
        iteration of the agent's main functionality.
        
        Returns:
            None
        """
        pass

    @abstractmethod
    def isRunning(self) -> bool:
        """
        Check if the agent should continue running.
        
        This method is called after each runPeriodic() call to determine if the
        agent should continue executing. Return True to keep running or False to
        stop the agent.
        
        Returns:
            bool: True if agent should continue running, False otherwise
        """
        pass

    # ----- Properties -----

    @abstractmethod
    def getName(self) -> str:
        """
        Get the display name of the agent.
        
        This name is used for logging, debugging, and UI display purposes.
        It should be short, descriptive, and unique among all agents.
        
        Returns:
            str: The agent's name
        """
        pass

    @abstractmethod
    def getDescription(self) -> str:
        """
        Get a description of the agent's purpose.
        
        This description is used for documentation and UI display purposes.
        It should briefly explain what the agent does.
        
        Returns:
            str: A brief description of the agent's purpose
        """
        pass

    # ----- Optional Methods -----

    def getIntervalMs(self) -> int:
        """
        Get the desired time interval between runPeriodic calls.
        
        This method specifies how long the system should wait between calls to
        runPeriodic(). The default implementation returns 0, meaning no delay.
        
        Returns:
            int: The time to wait in milliseconds between runPeriodic calls
            
        Note:
            Override this method to control the execution rate of your agent.
            A value of 0 means the agent will run as fast as possible.
        """
        # can leave as None, will use default time of 1 ms
        return self.DEFAULT_LOOP_TIME

    def forceShutdown(self) -> None:
        """
        Perform emergency shutdown tasks.
        
        This method is called when the agent needs to be stopped immediately,
        such as during a system shutdown or when an error occurs. It should quickly
        release any critical resources, abort operations, and prepare for termination.
        
        The default implementation does nothing. Override this method to handle
        resources that need special shutdown handling.
        
        Returns:
            None
        """
        # optional code to kill agent immediately here
        pass

    def onClose(self) -> None:
        """
        Perform cleanup tasks when the agent is being closed.
        
        This method is called once when the agent is being terminated, either
        after isRunning() returns False or after forceShutdown(). It should release
        all resources acquired by the agent, close files/connections, and ensure
        a clean shutdown.
        
        The default implementation does nothing. Override this method to clean up
        resources allocated during create() or runPeriodic().
        
        Returns:
            None
        """
        # optional agent cleanup here
        pass
