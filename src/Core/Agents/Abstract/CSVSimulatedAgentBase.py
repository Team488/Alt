"""
CSV Simulated Agent Base Module - For agents that use CSV logs to simulate robot position

This module provides the CsvSimulatedAgentBase class, which extends the CameraUsingAgentBase
to add simulation capabilities based on CSV log files. It allows the system to replay
recorded robot movements from CSV files while processing camera inputs, enabling
simulation and testing without a physical robot.

Key features:
- Replay of robot movement data from CSV log files
- Synchronization of log data with camera frames
- Support for time offset adjustment to align different data sources
- Conditional operation based on whether running on a robot or in simulation
- Position extraction and conversion to the system's internal coordinate format

This class is useful for testing and development scenarios where replaying recorded
robot movements alongside visual data is needed.
"""

from Core.Agents.Abstract import CameraUsingAgentBase
from tools.CsvParser import CsvParser, ROBOTPOSITIONKEYS
from Captures import FileCapture


class CsvSimulatedAgentBase(CameraUsingAgentBase):
    """
    Base class for agents that simulate robot movement using CSV log files.
    
    This class extends CameraUsingAgentBase to add simulation capabilities based on 
    CSV log files. It reads robot position data from the CSV file and makes it 
    available to the agent as if it were coming from a real robot.
    
    The inheritance hierarchy is:
    Agent -> CameraUsingAgentBase -> CsvSimulatedAgentBase
    
    Attributes:
        csvPath: Path to the CSV file containing robot log data
        timeOffsetS: Time offset in seconds to align CSV data with other data sources
        isOnRobot: Flag indicating whether this is running on a robot or in simulation
        parser: CSV parser object for reading log data
        timePassed: Elapsed simulation time in seconds
        secPerFrame: Time interval between frames in seconds
        robotPose2dCMRAD: Current robot pose (x, y, rotation) in (cm, cm, rad) format
    """
    def __init__(self, **kwargs):
        """
        Initialize a new CsvSimulatedAgentBase instance.
        
        Args:
            **kwargs: Keyword arguments that must include:
                robotLogCsvPath: Path to the CSV file with robot position data
                csvAlignmentOffsetS: Time offset in seconds for aligning data
                isOnRobot: Whether this is running on a robot or in simulation
                And other arguments required by parent classes
        """
        super().__init__(**kwargs)
        self.csvPath = kwargs.get("robotLogCsvPath", None)
        self.timeOffsetS = kwargs.get("csvAlignmentOffsetS", None)
        self.isOnRobot = kwargs.get("isOnRobot", None)

    def create(self):
        """
        Initialize simulation resources based on configuration.
        
        This method is called during agent initialization and sets up the
        CSV parser if running in simulation mode. If not in simulation mode,
        it simply initializes the robot pose to zeros.
        
        The method:
        1. Determines the time between frames based on camera FPS
        2. Creates a CSV parser configured with the appropriate keys
        3. Removes any zero entries at the start of the CSV data
        4. Initializes the simulation time counter
        
        If not running in simulation mode, the method simply initializes
        the robot pose to default values.
        """
        if self.isOnRobot:
            self.secPerFrame = 1 / self.capture.getFps()
            self.parser = CsvParser(
                self.csvPath, minTimestepS=self.secPerFrame, csvKeys=ROBOTPOSITIONKEYS
            )
            self.parser.removeZeroEntriesAtStart()
            self.timePassed = 0
        else:
            self.robotPose2dCMRAD = (0, 0, 0)

    def runPeriodic(self):
        """
        Execute the agent's periodic processing logic.
        
        This method is called regularly by the agent framework and updates
        the simulated robot position based on the current simulation time.
        If running in simulation mode, it:
        1. Gets the nearest position values from the CSV file for the current time
        2. Extracts the rotation and position values
        3. Converts the position from meters to centimeters
        4. Updates the internal robot pose representation
        
        If not running in simulation mode, this method does nothing additional
        beyond the parent class behavior.
        """
        super().runPeriodic()

        if self.isOnRobot:
            # Get CSV data for the current simulation time, adjusted by offset
            values = self.parser.getNearestValues(self.timePassed + self.timeOffsetS)
            
            # Extract position data based on key order
            # Rotation was first when we provided the CSV keys
            rotationRad = float(values[0][1][1])
            positionXCM = int(float(values[1][1][1]) * 100)  # Convert m -> cm
            positionYCM = int(float(values[2][1][1]) * 100)  # Convert m -> cm
            
            # Update the robot pose with the new values
            self.robotPose2dCMRAD = (positionXCM, positionYCM, rotationRad)
            
            # Update simulation time counter (would typically be done here)
            # self.timePassed += self.secPerFrame
        else:
            # Nothing to do in non-simulation mode
            pass
