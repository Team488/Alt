"""
Path Planning Agent Base Module - Base class for path generation and navigation agents

This module provides the PathPlanningAgentBase class, which extends the
PositionLocalizingAgentBase to add path planning functionality. It establishes 
the infrastructure for computing, visualizing, and sharing navigation paths with 
other components in the system.

Key features:
- Abstract interface for implementing various path planning algorithms
- Mechanism for sharing computed paths with other system components
- Visualization of paths overlaid on object maps
- Integration with the robot's position tracking system
- Property-based configuration of path parameters

Concrete implementations must override the getPath method to implement specific 
path planning algorithms, such as A* search, potential fields, or RRT.
"""

from abc import abstractmethod
from typing import List, Tuple, Optional, Any
import cv2
import numpy as np
from Core.Agents.Abstract.PositionLocalizingAgentBase import PositionLocalizingAgentBase
from tools import XTutils


class PathPlanningAgentBase(PositionLocalizingAgentBase):
    """
    Base class for path planning agents that generate navigation paths.
    
    This abstract base class extends PositionLocalizingAgentBase to add path planning
    functionality. It provides mechanisms for computing, visualizing, and sharing
    paths with other components in the system. Concrete implementations must override
    the getPath method to implement specific path planning algorithms.
    
    The inheritance hierarchy is:
    Agent -> PositionLocalizingAgentBase -> PathPlanningAgentBase
    
    Attributes:
        SHAREDPATHNAME: Key used to store paths in shared memory
        pathTable: Property for storing the path name in the property system
        path: The currently computed path as a list of (x,y) coordinates
        runFlag: Flag to control execution loop
        central: Reference to the Central system
    """

    SHAREDPATHNAME: str = "createdPath"

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a new PathPlanningAgentBase instance.
        
        Args:
            **kwargs: Keyword arguments passed to parent class constructor
        """
        super().__init__(**kwargs)
        self.pathTable = None
        self.path: Optional[List[Tuple[int, int]]] = None
        self.runFlag: bool = True
        self.central = None

    def create(self) -> None:
        """
        Initialize path planning resources.
        
        This method is called during agent initialization and sets up the
        property for storing path information in the network property system.
        
        Raises:
            ValueError: If PropertyOperator is not initialized
        """
        super().create()
        
        if self.propertyOperator is None:
            raise ValueError("PropertyOperator not initialized")
            
        self.pathTable = self.propertyOperator.createProperty(
            "Path_Name", "target_waypoints"
        )

    @abstractmethod
    def getPath(self) -> Optional[List[Tuple[int, int]]]:
        """
        Calculate a path based on current system state.
        
        This abstract method must be implemented by concrete subclasses to provide
        specific path planning algorithms. The method should return a list of (x,y)
        coordinates representing waypoints in the path, or None if no valid path
        can be generated.
        
        Returns:
            A list of (x,y) coordinate tuples representing the path,
            or None if no path can be generated
        """
        pass

    def __emitPath(self, path: Optional[List[Tuple[int, int]]]) -> None:
        """
        Share the calculated path with other components of the system.
        
        This method:
        1. Stores the path in shared memory for other agents to access
        2. Publishes the path to the network property system for visualization
           and telemetry purposes
        
        Args:
            path: The path to share (list of coordinate tuples) or None if no path
            
        Raises:
            ValueError: If required components are not initialized
        """
        if self.shareOp is None:
            raise ValueError("ShareOperator not initialized")
            
        if self.xclient is None:
            raise ValueError("XTablesClient not initialized")
            
        if self.Sentinel is None:
            raise ValueError("Logger not initialized")
            
        if self.pathTable is None:
            raise ValueError("Path table property not initialized")
            
        # put in shared memory (regardless if not created Eg. None)
        self.shareOp.put(PathPlanningAgentBase.SHAREDPATHNAME, path)
        # put on network if path was sucessfully created
        if path:
            self.Sentinel.info("Generated path")
            xcoords = XTutils.getCoordinatesAXCoords(path)
            self.xclient.putCoordinates(self.pathTable.get(), xcoords)
        # else:
        # instead of leaving old path, i think its best to make it clear we dont have a path
        # self.Sentinel.info("Failed to generate path")
        # self.xclient.putCoordinates(self.pathTable.get(), [])

    def runPeriodic(self) -> None:
        """
        Execute the path planning cycle.
        
        This method is called periodically and:
        1. Calls getPath() to calculate a new path if connected to localization
        2. Shares the calculated path with other components
        3. Visualizes the path and object map if available
        
        The method ensures that path planning only occurs when the agent has
        valid localization data.
        """
        super().runPeriodic()
        if self.connectedToLoc:
            self.path = self.getPath()
        else:
            self.path = None

        # emit the path to shared mem and network
        self.__emitPath(self.path)

        # Visualization code - creates a visual representation of the object map and path
        if self.central is None or not hasattr(self.central, 'objectmap'):
            return
            
        # Get the heat maps from the object map and create a visualization frame
        maps = self.central.objectmap.getHeatMaps()
        maps.append(np.zeros_like(self.central.objectmap.getHeatMap(0)))
        frame = cv2.merge(maps)

        # Draw the path as white circles on the visualization
        if self.path:
            for point in self.path:
                cv2.circle(frame, point, 5, (255, 255, 255), -1)
        frame = cv2.flip(frame, 0)  # Flip for correct orientation
        
        # Add debug message if no path is available
        if not self.path:
            cv2.putText(
                frame,
                f"No path! Localization Connected?: {self.connectedToLoc}",
                (int(frame.shape[0] / 2), int(frame.shape[0] / 2)),
                0,
                1,
                (255, 255, 255),
                1,
            )
        # Add legend for color coding
        cv2.putText(
            frame,
            "Game Objects: Blue | Robots : Red | Path : White",
            (10, 20),
            0,
            1,
            (255, 255, 255),
            2,
        )

        # Display each object type's heat map separately
        for idx, label in enumerate(self.central.objectmap.labels):
            cv2.imshow(str(label), self.central.objectmap.getHeatMap(idx))

        # Display the combined visualization
        cv2.imshow("pathplanner", frame)
        # Check for 'q' key press to stop the agent
        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.runFlag = False
