import sys
import os
import threading
import traceback
import time
from logging import Logger
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Any, Dict, Optional, Callable, Set, cast
from JXTABLES.XTablesClient import XTablesClient
import concurrent
from Core.TimeOperator import TimeOperator, Timer
from abstract.Agent import Agent
from Core.PropertyOperator import PropertyOperator, ReadonlyProperty


# subscribes to command request with xtables and then executes when requested
class AgentOperator:
    def __init__(
        self, propertyOp: PropertyOperator, timeOp: TimeOperator, logger: Logger
    ) -> None:
        self.Sentinel: Logger = logger
        self.propertyOp: PropertyOperator = propertyOp
        self.timeOp: TimeOperator = timeOp
        self.__executor: ThreadPoolExecutor = ThreadPoolExecutor()
        self.__futures: Dict[int, Future] = {}
        self.__futPtr: int = 0
        self.__futureLock: threading.Lock = threading.Lock()
        self.__stop: bool = False  # flag
        self.__runOnFinish: Optional[Callable[[], None]] = None  # runnable
        self.__setStatus: Callable[[str, str], bool] = (
            lambda agentName, status: propertyOp.createCustomReadOnlyProperty(
                f"active_agents.{agentName}.Status", status
            ).set(status)
        )
        self.__setErrorLog: Callable[[str, str], bool] = (
            lambda agentName, error: propertyOp.createCustomReadOnlyProperty(
                f"active_agents.{agentName}.Errors", error
            ).set(error)
        )
        self.__setDescription: Callable[[str, str], bool] = (
            lambda agentName, description: propertyOp.createCustomReadOnlyProperty(
                f"active_agents.{agentName}.Description", description
            ).set(description)
        )
        self.mainAgent: Optional[Agent] = None

    def stopAndWait(self) -> None:
        """Stop all agents but allow them to clean up, and wait for them to finish"""
        self.__stop = True
        self.waitForAgentsToFinish()
        self.__stop = False

    def stopPermanent(self) -> None:
        """Set the stop flag permanently (will not be reset)"""
        self.__stop = True

    def wakeAgentMain(self, agent: Agent) -> None:
        """Starts agent on whatever thread this is called from. Eg Likely Main"""
        self.Sentinel.info(
            f"Waking agent! | Name: {agent.getName()} Description : {agent.getDescription()}"
        )
        self.__setDescription(agent.getName(), agent.getDescription())
        self.__setStatus(agent.getName(), "starting")
        self.Sentinel.info("The agent is alive!")

        self.mainAgent = agent
        self.__startAgentLoop(agent, futurePtr=None)
        self.mainAgent = None

    def wakeAgent(self, agent: Agent) -> None:
        """Start an agent in a separate thread"""
        self.Sentinel.info(
            f"Waking agent! | Name: {agent.getName()} Description : {agent.getDescription()}"
        )
        self.__setDescription(agent.getName(), agent.getDescription())
        self.__setStatus(agent.getName(), "starting")
        future: Future = self.__executor.submit(self.__startAgentLoop, agent, self.__futPtr)
        with self.__futureLock:
            self.__futures[self.__futPtr] = future
        self.__futPtr += 1
        # grace period for thread to start
        self.Sentinel.info("The agent is alive!")

    def __startAgentLoop(self, agent: Agent, futurePtr: Optional[int]) -> None:
        """Main agent loop that manages agent lifecycle"""
        failed: bool = False
        progressStr: str = "starting"
        timer: Timer = agent.getTimer()

        """Main part #1 Creation and running"""
        try:
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
                    intervalMs: int = agent.getIntervalMs()
                    if intervalMs > 0:
                        sleepTime: float = intervalMs / 1000  # ms -> seconds
                        time.sleep(sleepTime)

        except Exception as e:
            failed = True
            self.__handleException(progressStr, agent.getName(), e)

        """ Main part #2 possible shutdown"""
        # if thread was shutdown abruptly (self.__stop flag), perform shutdown
        # shutdown before onclose

        forceStopped: bool = self.__stop
        if forceStopped:
            progressStr = "shutdown interrupt"
            self.__setStatus(agent.getName(), progressStr)
            self.Sentinel.debug("Shutting down agent")
            try:
                with timer.run("shutdown"):
                    agent.forceShutdown()
                    agent.hasShutdown = True
            except Exception as e:
                failed = True
                self.__handleException("shutdown", agent.getName(), e)

        elif not failed:
            self.__setStatus(
                agent.getName(), f"agent isRunning returned false (Not an error)"
            )
            self.Sentinel.debug(f"agent isRunning returned false (Not an error)")

        else:
            self.__setStatus(agent.getName(), f"agent failed during {progressStr}")
            self.Sentinel.debug(f"agent failed during {progressStr}")

        """ Main part #3 Cleanup"""
        try:
            # cleanup
            with timer.run("cleanup"):
                agent.onClose()
                agent.hasClosed = True

        except Exception as e:
            self.__handleException("cleanup", agent.getName(), e)

        # potentially run a task on agent finish
        if not self.__stop and self.__runOnFinish is not None:
            self.__runOnFinish()
            # clear
            self.__runOnFinish = None

        # close agent future if exists
        if futurePtr is not None:
            with self.__futureLock:
                self.__futures.pop(futurePtr)

    def __handleException(self, task: str, agentName: str, exception: Exception) -> None:
        """Handle an exception that occurred during agent execution"""
        message: str = f"Failed! | During {task}: {exception}"
        self.__setStatus(agentName, message)
        tb: str = traceback.format_exc()
        self.__setErrorLog(agentName, tb)
        self.Sentinel.error(tb)

    def setOnAgentFinished(self, runOnFinish: Callable[[], None]) -> None:
        """Set a callback to run when an agent finishes"""
        if self.__futures:
            self.__runOnFinish = runOnFinish
        else:
            self.Sentinel.warning("Neo has no agents yet!")

    def waitForAgentsToFinish(self) -> None:
        """Thread blocking method that waits for any running agents"""
        if self.__futures:
            self.Sentinel.info("Waiting for async agent to finish...")
            while True:
                with self.__futureLock:
                    if not self.__futures:
                        break
                time.sleep(0.001)
            self.Sentinel.info("Agents have all finished.")
        else:
            self.Sentinel.warning("No threadpool agents to wait for!")

        if self.mainAgent is not None:
            if not self.mainAgent.hasShutdown:
                with self.mainAgent.getTimer().run("shutdown"):
                    self.Sentinel.info("Shutting agent down with sigint")
                self.mainAgent.forceShutdown()
            if not self.mainAgent.hasClosed:
                self.Sentinel.info("Closing agent with sigint")
                with self.mainAgent.getTimer().run("cleanup"):
                    self.mainAgent.onClose()

            self.Sentinel.info("Main agent finished")

    def shutDownNow(self) -> None:
        """Threadblocks until executor is finished"""
        self.__executor.shutdown(wait=True, cancel_futures=True)
