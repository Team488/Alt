import time
from logging import Logger
from Core.LogManager import getLogger
from Core.PropertyOperator import PropertyOperator, ReadonlyProperty

class TimeOperator:
    TIMEPREFIX = "timers"
    def __init__(self, propertyOp : PropertyOperator, logger: Logger):
        self.Sentinel = logger
        self.__propertyOp = propertyOp
        self.timerMap = {}

    def getTimer(self, timeName):
        if timeName in self.timerMap:
            return self.timerMap.get(timeName)
        
        timer = self.__createTimer(timeName)
        self.timerMap[timeName] = timer
        return timer

    def __createTimer(self, timeName):
        timeTable = self.__propertyOp.getChild(f"{TimeOperator.TIMEPREFIX}.{timeName}")
        return Timer(timeName, timeTable)        


from contextlib import contextmanager

Sentinel = getLogger("Timer_Entry")
class Timer:
    def __init__(self, name, timeTable : PropertyOperator):
        self.name = name
        self.timeMap = {}
        self.resetMeasurement()
        self.timeTable = timeTable

    def getName(self):
        return self.name
    
    def resetMeasurement(self, subTimerName="main"):
        self.timeMap[subTimerName] = time.perf_counter()

    def measureAndUpdate(self, subTimerName="main"):
        lastStart = self.timeMap.get(subTimerName)
        if lastStart is None:
            Sentinel.warning("subTimer has not been reset to a value yet! Please make sure resetMeasurement() is called first")
            return
        
        dS = time.perf_counter()-lastStart
        dMs = dS*1000
        self.timeTable.createCustomReadOnlyProperty(f"{subTimerName}_Ms:", addBasePrefix=True, addOperatorPrefix=True).set(dMs)

    def markDeactive(self, subTimerName="main"):
        self.timeTable.createCustomReadOnlyProperty(f"{subTimerName}_Ms:", addBasePrefix=True, addOperatorPrefix=True).set("Inactive")

    @contextmanager
    def run(self, subTimerName="main"):
        """ Concise way start a timer.\n Equivalent to:\n
            Timer.resetMeasurement(subTimerName)
            {Timed Code Here}
            Timer.measureAndUpdate(subTimerName)
            
            By Doing:
            with timer.run(subTimerName):
                {Timed Code Here}
        """
        self.resetMeasurement(subTimerName)
        try:
            yield
        finally:
            self.measureAndUpdate(subTimerName)
