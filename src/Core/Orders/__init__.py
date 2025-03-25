"""
Orders Package - Task specifications that can be dispatched to agents

This package contains Order classes that define specific tasks or operations to be
performed by compatible agents. Orders represent a command pattern implementation
where:

- Each Order encapsulates a specific task or operation
- Orders are dispatched to agents that can fulfill them
- Orders can carry parameters that customize their behavior
- Orders provide a way to decouple task definition from execution

The Orders system allows for dynamic task allocation and execution, where the
Central coordinator can dispatch different tasks to agents based on system state
and requirements.

Example orders include:
- TargetUpdatingOrder: Updates target locations for navigation
- OrderExample: Demonstrates the basic Order implementation pattern
"""

from .OrderExample import OrderExample
from .TargetUpdatingOrder import TargetUpdatingOrder
