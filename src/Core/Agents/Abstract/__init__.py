"""
Abstract Agent Base Classes - Interface definitions for system agents

This package contains abstract base classes that define interfaces and provide
common functionality for the various agent types in the system. These base classes:

- Define required methods that concrete agents must implement
- Provide common utility methods to reduce code duplication
- Establish standard patterns for agent behavior and communication
- Enable composition of capabilities through multiple inheritance

By inheriting from these base classes, concrete agent implementations ensure
they conform to expected interfaces while gaining access to shared functionality.

Key abstract base classes include:
- CameraUsingAgentBase: For agents that process camera input
- InferenceAgent: For agents that perform ML inference on images
- ObjectLocalizingAgentBase: For agents that detect and track objects
- PathPlanningAgentBase: For agents that calculate navigation paths
- PositionLocalizingAgentBase: For agents that determine positions
- ReefTrackingAgentBase: For agents that track reef elements
- TimestampRegulatedAgentBase: For agents that operate on timed intervals
"""

from .CameraUsingAgentBase import CameraUsingAgentBase
from .InferenceAgent import InferenceAgent, InferenceAgentPartial
from .ObjectLocalizingAgentBase import (
    ObjectLocalizingAgentBase,
    ObjectLocalizingAgentPartial,
)
from .PathPlanningAgentBase import PathPlanningAgentBase
from .PositionLocalizingAgentBase import PositionLocalizingAgentBase
from .ReefTrackingAgentBase import ReefTrackingAgentBase, ReefTrackingAgentPartial
from .TimestampRegulatedAgentBase import TimestampRegulatedAgentBase
