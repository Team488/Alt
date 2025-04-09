import time
from logging import Logger
from typing import Dict, Generator
from .LogOperator import getChildLogger
from .PropertyOperator import PropertyOperator
from .LogOperator import getChildLogger

Sentinel = getChildLogger("Time Operator")


class TimeOperator:
    """
    Manages timing operations for performance monitoring
    """

    TIMENAME: str = "timers"

    def __init__(self, propertyOp: PropertyOperator) -> None:
        self.__propertyOp: PropertyOperator = propertyOp
        self.timerMap: Dict[str, "Timer"] = {}

    def getTimer(self, timeName: str = TIMENAME) -> "Timer":
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

    def __createTimer(self, timeName: str) -> "Timer":
        """
        Create a new timer with the given name

        Args:
            timeName: The name of the timer to create

        Returns:
            A new Timer instance
        """
        timeTable = self.__propertyOp.getChild(timeName)
        if timeTable is None:
            raise ValueError(f"Could not create property child for timer {timeName}")
        return Timer(timeName, timeTable)


from contextlib import contextmanager

Sentinel: Logger = getChildLogger("Timer_Entry")


class Timer:
    """
    Measures and records performance timing information
    """

    def __init__(self, name: str, timeTable: PropertyOperator) -> None:
        self.name: str = name
        self.timeMap: Dict[str, float] = {}
        self.resetMeasurement()
        self.timeTable: PropertyOperator = timeTable

    def getName(self) -> str:
        """Get the name of this timer"""
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
