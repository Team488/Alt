"""
Time Operator Module - Provides timing and performance measurement utilities

This module defines the TimeOperator and Timer classes used for measuring and
tracking execution time throughout the codebase. It enables performance monitoring,
benchmarking, and optimization by providing tools to measure execution times of
different code sections.

The module creates a hierarchical timing structure where:
- TimeOperator manages a collection of named timers
- Each Timer can have multiple sub-timers for more granular timing

Usage examples:
    # Get a timer and use it directly
    timer = timeOperator.getTimer("myOperation")
    timer.resetMeasurement()
    # ... code to time ...
    timer.measureAndUpdate()
    
    # Or use the context manager for cleaner code
    with timeOperator.getTimer("myOperation").run():
        # ... code to time ...
"""

import time
from logging import Logger
from typing import Dict, Optional, Generator, Any
from Core.LogManager import getLogger
from Core.PropertyOperator import PropertyOperator, ReadonlyProperty


class TimeOperator:
    """
    Manages timing operations for performance monitoring.
    
    This class provides a centralized system for creating and managing timers
    used to measure execution time of various operations in the system.
    
    Attributes:
        TIMEPREFIX: Prefix used for timer properties in the property tree
        Sentinel: Logger instance for this operator
        timerMap: Dictionary mapping timer names to Timer instances
    """
    TIMEPREFIX: str = "timers"

    def __init__(self, propertyOp: PropertyOperator, logger: Logger) -> None:
        """
        Initialize a TimeOperator instance.
        
        Args:
            propertyOp: PropertyOperator to store timer values
            logger: Logger instance for this operator
        """
        self.Sentinel: Logger = logger
        self.__propertyOp: PropertyOperator = propertyOp
        self.timerMap: Dict[str, 'Timer'] = {}

    def getTimer(self, timeName: str) -> 'Timer':
        """
        Get a timer with the given name, creating it if it doesn't exist
        
        Args:
            timeName: The name of the timer to get or create
            
        Returns:
            A Timer instance for the given name
        """
        if timeName in self.timerMap:
            return self.timerMap.get(timeName)

        timer = self.__createTimer(timeName)
        self.timerMap[timeName] = timer
        return timer

    def __createTimer(self, timeName: str) -> 'Timer':
        """
        Create a new timer with the given name
        
        Args:
            timeName: The name of the timer to create
            
        Returns:
            A new Timer instance
        """
        timeTable = self.__propertyOp.getChild(f"{TimeOperator.TIMEPREFIX}.{timeName}")
        if timeTable is None:
            raise ValueError(f"Could not create property child for timer {timeName}")
        return Timer(timeName, timeTable)


from contextlib import contextmanager

Sentinel: Logger = getLogger("Timer_Entry")


class Timer:
    """
    Measures and records performance timing information.
    
    This class provides functionality to measure execution time of code sections
    and record the results in a property tree. It supports multiple named sub-timers
    within a single Timer instance to track different components of an operation.
    
    Attributes:
        name: The name of this timer
        timeMap: Dictionary mapping sub-timer names to their start times
        timeTable: PropertyOperator for storing timing measurements
    """
    def __init__(self, name: str, timeTable: PropertyOperator) -> None:
        """
        Initialize a Timer instance.
        
        Args:
            name: The name of this timer
            timeTable: PropertyOperator for storing timing measurements
        """
        self.name: str = name
        self.timeMap: Dict[str, float] = {}
        self.resetMeasurement()
        self.timeTable: PropertyOperator = timeTable

    def getName(self) -> str:
        """
        Get the name of this timer.
        
        Returns:
            str: The name of this timer
        """
        return self.name

    def resetMeasurement(self, subTimerName: str = "main") -> None:
        """
        Reset the measurement for the given sub-timer
        
        Args:
            subTimerName: Name of the sub-timer to reset (defaults to "main")
        """
        self.timeMap[subTimerName] = time.perf_counter()

    def measureAndUpdate(self, subTimerName: str = "main") -> None:
        """
        Measure elapsed time since reset and update the timer property
        
        Args:
            subTimerName: Name of the sub-timer to measure (defaults to "main")
        """
        lastStart = self.timeMap.get(subTimerName)
        if lastStart is None:
            Sentinel.warning(
                "subTimer has not been reset to a value yet! Please make sure resetMeasurement() is called first"
            )
            return

        dS = time.perf_counter() - lastStart
        dMs = dS * 1000
        self.timeTable.createCustomReadOnlyProperty(
            f"{subTimerName}_Ms:", addBasePrefix=True, addOperatorPrefix=True
        ).set(dMs)

    def markDeactive(self, subTimerName: str = "main") -> None:
        """
        Mark a sub-timer as inactive
        
        Args:
            subTimerName: Name of the sub-timer to mark inactive (defaults to "main")
        """
        self.timeTable.createCustomReadOnlyProperty(
            f"{subTimerName}_Ms:", addBasePrefix=True, addOperatorPrefix=True
        ).set("Inactive")

    @contextmanager
    def run(self, subTimerName: str = "main") -> Generator[None, None, None]:
        """
        Concise way start a timer.\n Equivalent to:\n
        Timer.resetMeasurement(subTimerName)
        {Timed Code Here}
        Timer.measureAndUpdate(subTimerName)

        By Doing:
        with timer.run(subTimerName):
            {Timed Code Here}
            
        Args:
            subTimerName: Name of the sub-timer to run (defaults to "main")
            
        Yields:
            Nothing, used as a context manager
        """
        self.resetMeasurement(subTimerName)
        try:
            yield
        finally:
            self.measureAndUpdate(subTimerName)
