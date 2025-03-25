"""
Agents Package - Implementation of specialized system agents

This package contains all the specialized agent implementations that perform
specific operational tasks within the system. Each agent is responsible for a
distinct capability, such as:

- Path planning and navigation
- Computer vision and object detection
- Reef position tracking
- Sensor data processing
- Calibration and configuration
- User interaction and visualization

Agents operate within the framework provided by the Core package, interfacing
with the Central coordination system and communicating through defined channels
like properties, shared memory, and orders.

Each agent typically inherits from appropriate base classes in the Abstract
subpackage that define required interfaces and provide common functionality.
"""

from .AgentExample import AgentExample
from .OrangePiAgent import OrangePiAgent
from .PathPlanningAgents import (
    DriveToTargetAgent,
    DriveToFixedPointAgent,
    DriveToNetworkTargetAgent,
)
from .FrameDisplayer import FrameDisplayer
from .CalibrationController import CalibrationController
from .InteractivePathPlanner import InteractivePathPlanner
from .ReefAndObjectLocalizer import ReefAndObjectLocalizerPartial
