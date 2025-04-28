import time
from logging import Logger
from typing import Dict, Generator
from .LogOperator import getChildLogger
from .PropertyOperator import PropertyOperator

Sentinel = getChildLogger("Time Operator")

class TimeOperator:
    """
    Manages timing operations for performance monitoring.

    This class is responsible for creating and managing timers,
    allowing performance measurements to be taken during execution.
    It uses the PropertyOperator to store timing information.
    """

    TIMENAME: str = "timers"

    def __init__(self, propertyOp: PropertyOperator) -> None:
        """
        Initializes the TimeOperator with a PropertyOperator.

        Args:
            propertyOp (PropertyOperator): PropertyOperator instance used to manage timing properties.
        """
        self.__propertyOp: PropertyOperator = propertyOp
        self.timerMap: Dict[str, "Timer"] = {}

    def getTimer(self, timeName: str = TIMENAME) -> "Timer":
        """
        Get a timer with the given name, creating it if it doesn't exist.

        Args:
            timeName (str): The name of the timer to get or create.

        Returns:
            Timer: An instance of Timer for the specified name.
        """
        if timeName in self.timerMap:
            return self.timerMap.get(timeName)
        timer = self.__createTimer(timeName)
        self.timerMap[timeName] = timer
        return timer

    def __createTimer(self, timeName: str) -> "Timer":
        """
        Create a new timer with the given name.

        Args:
            timeName (str): The name of the timer to create.

        Returns:
            Timer: A new Timer instance.

        Raises:
            ValueError: If a property child for the specified timer name cannot be created.
        """
        timeTable = self.__propertyOp.getChild(timeName)
        if timeTable is None:
            raise ValueError(f"Could not create property child for timer {timeName}")
        return Timer(timeName, timeTable)

from contextlib import contextmanager

Sentinel: Logger = getChildLogger("Timer_Entry")

class Timer:
    """
    Measures and records performance timing information.

    This class is responsible for managing individual timing,
    allowing for the measurement of elapsed time for specific
    sub-timers and storing this information using a PropertyOperator.
    """

    def __init__(self, name: str, timeTable: PropertyOperator) -> None:
        """
        Initializes a Timer instance.

        Args:
            name (str): The name of the timer.
            timeTable (PropertyOperator): PropertyOperator instance to manage timing properties.
        """
        self.name: str = name
        self.timeMap: Dict[str, float] = {}
        self.resetMeasurement()
        self.timeTable: PropertyOperator = timeTable

    def getName(self) -> str:
        """Get the name of this timer."""
        return self.name

    def resetMeasurement(self, subTimerName: str = "main") -> None:
        """
        Reset the measurement for the given sub-timer.

        Args:
            subTimerName (str): Name of the sub-timer to reset (defaults to "main").
        """
        self.timeMap[subTimerName] = time.perf_counter()

    def measureAndUpdate(self, subTimerName: str = "main") -> None:
        """
        Measure elapsed time since reset and update the timer property.

        Args:
            subTimerName (str): Name of the sub-timer to measure (defaults to "main").
        """
        lastStart = self.timeMap.get(subTimerName)
        if lastStart is None:
            Sentinel.warning(
                "subTimer has not been reset to a value yet! Please make sure resetMeasurement() is called first."
            )
            return
        dS = time.perf_counter() - lastStart
        dMs = dS * 1000
        self.timeTable.createCustomReadOnlyProperty(
            f"{subTimerName}_Ms:", addBasePrefix=True, addOperatorPrefix=True
        ).set(dMs)

    def markDeactive(self, subTimerName: str = "main") -> None:
        """
        Mark a sub-timer as inactive.

        Args:
            subTimerName (str): Name of the sub-timer to mark inactive (defaults to "main").
        """
        self.timeTable.createCustomReadOnlyProperty(
            f"{subTimerName}_Ms:", addBasePrefix=True, addOperatorPrefix=True
        ).set("Inactive")

    @contextmanager
    def run(self, subTimerName: str = "main") -> Generator[None, None, None]:
        """
        Context manager to start a timer for the duration of its block.

        It encapsulates the reset and update steps using a context manager.

        Args:
            subTimerName (str): Name of the sub-timer to run (defaults to "main").

        Yields:
            None: Used as a context manager.
        """
        self.resetMeasurement(subTimerName)
        try:
            yield
        finally:
            self.measureAndUpdate(subTimerName)