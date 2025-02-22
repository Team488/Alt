import sys
import os
import threading
import traceback
import time
from logging import Logger
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import Future
from JXTABLES.XTablesClient import XTablesClient
import concurrent
from Core.TimeOperator import TimeOperator
from abstract.Agent import Agent
from Core.PropertyOperator import PropertyOperator


# subscribes to command request with xtables and then executes when requested
class AgentOperator:
    def __init__(self, propertyOp: PropertyOperator, timeOp : TimeOperator, logger: Logger):
        self.Sentinel = logger
        self.propertyOp = propertyOp
        self.timeOp = timeOp
        self.__executor = ThreadPoolExecutor()
        self.__futures = {}
        self.__futPtr = 0
        self.__futureLock = threading.Lock()
        self.__stop = False  # flag
        self.__runOnFinish = None  # runnable
        self.__setStatus = (
            lambda agentName, status: propertyOp.createCustomReadOnlyProperty(
                f"active_agents.{agentName}.Status", status
            ).set(status)
        )
        self.__setErrorLog = (
            lambda agentName, error: propertyOp.createCustomReadOnlyProperty(
                f"active_agents.{agentName}.Errors", error
            ).set(error)
        )
        self.__setDescription = (
            lambda agentName, description: propertyOp.createCustomReadOnlyProperty(
                f"active_agents.{agentName}.Description", description
            ).set(description)
        )

    def stopAndWait(self):
        self.__stop = True
        self.waitForAgentsToFinish()
        self.__stop = False

    def stopPermanent(self):
        self.__stop = True

    def wakeAgentMain(self, agent: Agent):
        """Starts agent on whatever thread this is called from. Eg Likely Main"""
        self.Sentinel.info(
            f"Waking agent! | Name: {agent.getName()} Description : {agent.getDescription()}"
        )
        self.__setDescription(agent.getName(), agent.getDescription())
        self.__setStatus(agent.getName(), "starting")
        self.Sentinel.info("The agent is alive!")

        self.__startAgentLoop(agent, futurePtr=None)

    def wakeAgent(self, agent: Agent):
        self.Sentinel.info(
            f"Waking agent! | Name: {agent.getName()} Description : {agent.getDescription()}"
        )
        self.__setDescription(agent.getName(), agent.getDescription())
        self.__setStatus(agent.getName(), "starting")
        future = self.__executor.submit(self.__startAgentLoop, agent, self.__futPtr)
        with self.__futureLock:
            self.__futures[self.__futPtr] = future
        self.__futPtr += 1
        # grace period for thread to start
        self.Sentinel.info("The agent is alive!")

    def __startAgentLoop(self, agent: Agent, futurePtr: int):
        
        """ Main part #1 Creation and running"""
        try:
            timer = agent.getTimer()
            self.__setErrorLog(agent.getName(), "None...")
            
            # create
            progressStr = "create"
            self.__setStatus(agent.getName(), "creating")

            with timer.run("create"):
                agent.create()

            self.__setStatus(agent.getName(), "running")
            progressStr = "isRunning"
            while agent.isRunning():
                with timer.run("runPeriodic"):
                    if self.__stop:
                        break
                    progressStr = "runPeriodic"
                    agent.runPeriodic()

                    progressStr = "getIntervalMs"
                    intervalMs = agent.getIntervalMs()
                    if intervalMs > 0:
                        sleepTime = intervalMs / 1000  # ms -> seconds
                        time.sleep(sleepTime)

        except Exception as e:
            self.__handleException(progressStr,agent.getName(),e)


        """ Main part #2 possible shutdown"""
        # if thread was shutdown abruptly (self.__stop flag), perform shutdown
        # shutdown before onclose
        forceStopped = self.__stop
        if forceStopped:
            progressStr = "shutdown interrupt"
            self.__setStatus(agent.getName(), progressStr)
            self.Sentinel.debug("Shutting down agent")
            try:
                agent.forceShutdown()
            except Exception as e:
                self.__handleException("shutdown",agent.getName(),e)

        else:
            self.__setStatus(
                agent.getName(), f"agent isRunning returned false (Not an error)"
            )
            self.Sentinel.debug(f"agent isRunning returned false (Not an error)")
        
        """ Main part #3 Cleanup"""
        try:    
            # cleanup
            with timer.run("cleanup"):
                agent.onClose()

        except Exception as e:
            self.__handleException("cleanup",agent.getName(),e)
        

        # potentially run a task on agent finish
        if not self.__stop and self.__runOnFinish is not None:
            self.__runOnFinish()
            # clear
            self.__runOnFinish = None

        
        # close agent future if exists
        if futurePtr is not None:
            with self.__futureLock:
                self.__futures.pop(futurePtr)

    def __handleException(self, task: str, agentName: str, exception):
        message = f"Failed! | During {task}: {exception}"
        self.__setStatus(agentName, message)
        tb = traceback.format_exc()
        self.__setErrorLog(agentName, tb)
        self.Sentinel.error(tb)


    def setOnAgentFinished(self, runOnFinish):
        if self.__futures:
            self.__runOnFinish = runOnFinish
        else:
            self.Sentinel.warning("Neo has no agents yet!")

    def waitForAgentsToFinish(self):
        """Thread blocking method that waits for any running agents"""
        if self.__futures:
            self.Sentinel.info("Waiting for agent to finish...")
            while True:
                with self.__futureLock:
                    if not self.__futures:
                        break
                time.sleep(0.001)
            self.Sentinel.info("Agents have all finished.")
        else:
            self.Sentinel.warning("No agents to wait for!")

    def shutDownNow(self):
        """Threadblocks until executor is finished"""
        self.__executor.shutdown(wait=True, cancel_futures=True)
