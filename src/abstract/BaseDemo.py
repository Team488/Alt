"""
BaseDemo Module - Abstract interface for demonstration components.

This module defines the base interface for demonstrations, which are self-contained
components that showcase specific functionality of the system. Demonstrations
provide a way to test and demonstrate individual features without requiring
the full system to be running.

The Demo abstract base class provides a simple interface that all demonstration
implementations must follow.
"""

from abc import ABC, abstractmethod


class Demo(ABC):
    """
    Abstract base class for all demonstration implementations.
    
    Demonstrations are self-contained components that showcase specific
    functionality of the system. They provide a simple way to test and
    demonstrate individual features, algorithms, or subsystems without
    requiring the full system to be running.
    
    All demonstration classes must implement the startDemo method to
    define the entry point for the demonstration.
    """
    
    @abstractmethod
    def startDemo(self) -> None:
        """
        Start the demonstration.
        
        This method serves as the entry point for the demonstration.
        It should contain all the logic needed to run the demonstration,
        including initialization, execution, and cleanup.
        
        Returns:
            None
        """
        pass
