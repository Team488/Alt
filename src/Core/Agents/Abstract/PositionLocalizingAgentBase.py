"""
Position Localizing Agent Base Module - Base class for agents that track robot position

This module provides the PositionLocalizingAgentBase class, which extends the basic
Agent class with robot position tracking capabilities. It establishes a connection
to external position data sources (typically from robot odometry or vision systems)
and maintains the current robot position and orientation in multiple coordinate formats.

Key features:
- Subscribes to robot position updates from an external source (via XTables)
- Maintains the current robot position in both meters and centimeters
- Provides position offset adjustment capabilities for calibration
- Publishes position data to properties for other components to use
- Handles coordinate system transformations appropriately

This base class is typically used as a building block for more complex agents
that need to know the robot's position, such as object localizers, path planners,
and navigation agents.
"""

from typing import Tuple, Any, Optional
from abstract.Agent import Agent
from tools import NtUtils


class PositionLocalizingAgentBase(Agent):
    """
    Base class for agents that need robot position data.
    
    This abstract base class extends the basic Agent class with position
    localization capabilities. It subscribes to robot position updates from
    an external source (via XTables) and maintains the current robot position
    and orientation in multiple coordinate formats. It also provides position
    offset adjustment capabilities.
    
    The inheritance hierarchy is:
    Agent -> PositionLocalizingAgentBase
    
    Attributes:
        xtablesPosTable: Property for the XTables position table name
        locX: Property for robot X position (meters)
        locY: Property for robot Y position (meters)
        locRot: Property for robot rotation (radians)
        positionOffsetXM: User-adjustable X position offset (meters)
        positionOffsetYM: User-adjustable Y position offset (meters)
        positionOffsetYAWDEG: User-adjustable rotation offset (degrees)
        robotPose2dMRAD: Robot pose (X, Y, Rotation) in meters and radians
        robotPose2dCMRAD: Robot pose (X, Y, Rotation) in centimeters and radians
        connectedToLoc: Flag indicating connection to localization
        locTimeStamp: Timestamp of last position update
        
    Note:
        For changes to properties to take effect, the agent must be restarted
    """

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a new PositionLocalizingAgentBase instance.
        
        Sets up initial property values and robot pose variables.
        These will be properly initialized in the create() method.
        
        Args:
            **kwargs: Keyword arguments passed to parent class constructor
        """
        super().__init__(**kwargs)
        # Initialize properties that will be set in create()
        self.xtablesPosTable = None
        self.locX = None
        self.locY = None
        self.locRot = None
        self.positionOffsetXM = None
        self.positionOffsetYM = None
        self.positionOffsetYAWDEG = None
        
        # Initialize robot pose variables
        self.robotPose2dMRAD: Tuple[float, float, float] = (0, 0, 0)
        self.robotPose2dCMRAD: Tuple[float, float, float] = (0, 0, 0)
        self.connectedToLoc: bool = False
        self.locTimeStamp: int = -1

    def create(self) -> None:
        """
        Initialize localization properties and subscribe to position updates.
        
        This method:
        1. Creates properties for accessing and controlling the robot position
        2. Sets up network properties for XTables integration
        3. Subscribes to position updates from the robot
        
        Raises:
            ValueError: If required system components are missing
        """
        super().create()
        
        if self.propertyOperator is None:
            raise ValueError("PropertyOperator not initialized")
            
        if self.xclient is None:
            raise ValueError("XTablesClient not initialized")
            
        # create managing properties
        self.xtablesPosTable = self.propertyOperator.createProperty(
            propertyTable="xtablesPosTable", propertyDefault="PoseSubsystem.RobotPose"
        )

        self.locX = self.propertyOperator.createReadOnlyProperty("Robot.Robot_Loc_X", 0)
        self.locY = self.propertyOperator.createReadOnlyProperty("Robot.Robot_Loc_Y", 0)
        self.locRot = self.propertyOperator.createReadOnlyProperty("Robot.Robot_Rot", 0)

        self.positionOffsetXM = self.propertyOperator.createProperty(
            "Position_Offset_X_M", propertyDefault=0, loadIfSaved=False
        )
        self.positionOffsetYM = self.propertyOperator.createProperty(
            "Position_Offset_Y_M", propertyDefault=0, loadIfSaved=False
        )
        self.positionOffsetYAWDEG = self.propertyOperator.createProperty(
            "Position_Offset_YAW_Deg", propertyDefault=0, loadIfSaved=False
        )

        # Variable to store robot location. Units will be (X(m), Y(m), Yaw Rotation (rad))
        self.robotPose2dMRAD = (0, 0, 0)
        self.robotPose2dCMRAD = (0, 0, 0)
        self.connectedToLoc = False
        self.locTimeStamp = -1

        # Subscribe to position updates from XTables
        self.xclient.subscribe(self.xtablesPosTable.get(), self.__updateLocation)

    def __updateLocation(self, ret: Any) -> None:
        """
        Handle position updates from XTables.
        
        This callback is invoked when new position data is available from
        the robot. It updates the internal pose variables and publishes
        the updated values to network properties for other components.
        
        Args:
            ret: Data packet from XTables containing position information
        """
        if self.Sentinel is None:
            return
            
        try:
            # Parse the position data from bytes
            self.robotPose2dMRAD = NtUtils.getPose2dFromBytes(ret.value)
            # Convert to centimeters for internal use (maintaining radians for rotation)
            self.robotPose2dCMRAD = (
                self.robotPose2dMRAD[0] * 100,
                self.robotPose2dMRAD[1] * 100,
                self.robotPose2dMRAD[2],
            )  # m to cm

            # Update network properties with new position data
            if self.locX and self.locY and self.locRot:
                self.locX.set(self.robotPose2dMRAD[0])
                self.locY.set(self.robotPose2dMRAD[1])
                self.locRot.set(self.robotPose2dMRAD[2])
                
            # self.Sentinel.debug("Updated robot pose!!")
            self.connectedToLoc = True
        except Exception as e:
            self.Sentinel.debug(e)
            self.Sentinel.debug("Could not get robot pose!!")
            self.connectedToLoc = False
