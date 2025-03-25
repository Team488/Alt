"""
AgentOperator Module - Manages agent lifecycle and execution.

The AgentOperator is responsible for starting, running, and stopping agents.
It manages agent execution in both the main thread and background threads,
handles exceptions, and coordinates agent lifecycle events.

This module provides the infrastructure for executing agents in a controlled
environment, monitoring their status, and ensuring proper cleanup when agents
terminate.
"""

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
class AgentOperator:
    """
    Manages the lifecycle of agents in the system.
    
    The AgentOperator is responsible for starting, monitoring, and stopping agents.
    It can run agents in background threads or in the main thread, handle exceptions,
    and ensure proper cleanup of resources.
    
    Attributes:
        Sentinel (Logger): The logger used for recording agent activities
        propertyOp (PropertyOperator): Used to create and manage properties
        timeOp (TimeOperator): Used for timing operations
        mainAgent (Optional[Agent]): Reference to the agent running on main thread
    """
    def __init__(
        self, propertyOp: PropertyOperator, timeOp: TimeOperator, logger: Logger
    ) -> None:
        """
        Initialize a new AgentOperator.
        
        Args:
            propertyOp: PropertyOperator for creating and managing properties
            timeOp: TimeOperator for timing operations
            logger: Logger for recording activities and errors
        """
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
        """
        Stop all agents and wait for them to clean up and finish.
        
        This method sets the stop flag to true, waits for all agents to complete
        their shutdown sequence, and then resets the stop flag. This is a
        controlled shutdown that allows agents to clean up resources properly.
        
        Returns:
            None
        """
        self.__stop = True
        self.waitForAgentsToFinish()
        self.__stop = False

    def stopPermanent(self) -> None:
        """
        Set the stop flag permanently to shut down all agents.
        
        This method sets the stop flag to true permanently, signaling all agents
        to stop running. Unlike stopAndWait(), this method doesn't wait for agents
        to complete or reset the flag afterward.
        
        Returns:
            None
        """
        self.__stop = True

    def wakeAgentMain(self, agent: Agent) -> None:
        """
        Start an agent in the current thread (usually the main thread).
        
        This method runs the agent directly in the current thread, blocking until
        the agent completes. This is useful for agents that need to run in the main
        thread or for simple, short-lived agents that don't need background execution.
        
        Args:
            agent: The agent to run
            
        Returns:
            None
        """
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
        """
        Start an agent in a separate background thread.
        
        This method runs the agent in a background thread managed by the thread pool
        executor. The agent runs asynchronously, and this method returns immediately
        after scheduling the agent for execution.
        
        Args:
            agent: The agent to run in the background
            
        Returns:
            None
        """
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
        """
        The main execution loop for an agent's lifecycle.
        
        This private method implements the full agent lifecycle:
        1. Creation phase - calls agent.create()
        2. Running phase - repeatedly calls agent.runPeriodic() while agent.isRunning()
        3. Shutdown phase - calls agent.forceShutdown() if needed
        4. Cleanup phase - calls agent.onClose()
        
        It also handles exceptions, updates status properties, and manages timing.
        
        Args:
            agent: The agent to run
            futurePtr: Optional pointer to the agent's future in the futures dictionary
                      (None for main thread agents)
        
        Returns:
            None
        """
        failed: bool = False
        progressStr: str = "starting"
        timer: Timer = agent.getTimer()

        # Main part #1: Creation and running
        try:
            self.__setErrorLog(agent.getName(), "None...")

            # Creation phase
            progressStr = "create"
            self.__setStatus(agent.getName(), "creating")

            with timer.run("create"):
                agent.create()

            # Running phase
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

        # Main part #2: Possible shutdown
        # If thread was shutdown abruptly (self.__stop flag), perform shutdown
        # Shutdown is done before onclose

        forceStopped: bool = self.__stop
        if forceStopped:
            # Handle forced shutdown case
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
            # Normal termination: agent.isRunning() returned false
            self.__setStatus(
                agent.getName(), f"agent isRunning returned false (Not an error)"
            )
            self.Sentinel.debug(f"agent isRunning returned false (Not an error)")

        else:
            # Agent failed due to exception
            self.__setStatus(agent.getName(), f"agent failed during {progressStr}")
            self.Sentinel.debug(f"agent failed during {progressStr}")

        # Main part #3: Cleanup
        try:
            # Cleanup phase - always called regardless of how agent ended
            with timer.run("cleanup"):
                agent.onClose()
                agent.hasClosed = True

        except Exception as e:
            self.__handleException("cleanup", agent.getName(), e)

        # Run optional callback when agent finishes (only if not stopped externally)
        if not self.__stop and self.__runOnFinish is not None:
            self.__runOnFinish()
            # Clear callback after running it
            self.__runOnFinish = None

        # Remove agent's future from tracking map if running in background thread
        if futurePtr is not None:
            with self.__futureLock:
                self.__futures.pop(futurePtr)

    def __handleException(self, task: str, agentName: str, exception: Exception) -> None:
        """
        Handle an exception that occurred during agent execution.
        
        This private method logs the exception, updates the agent's status,
        and records the full stack trace.
        
        Args:
            task: The name of the task where the exception occurred
            agentName: The name of the agent that raised the exception
            exception: The exception that was raised
            
        Returns:
            None
        """
        message: str = f"Failed! | During {task}: {exception}"
        self.__setStatus(agentName, message)
        tb: str = traceback.format_exc()
        self.__setErrorLog(agentName, tb)
        self.Sentinel.error(tb)

    def setOnAgentFinished(self, runOnFinish: Callable[[], None]) -> None:
        """
        Set a callback to run when an agent finishes.
        
        This method registers a callback function that will be called when the
        next agent to finish completes. The callback is only registered if there
        are currently agents running.
        
        Args:
            runOnFinish: A callback function to run when an agent finishes
            
        Returns:
            None
        """
        if self.__futures:
            self.__runOnFinish = runOnFinish
        else:
            self.Sentinel.warning("Neo has no agents yet!")

    def waitForAgentsToFinish(self) -> None:
        """
        Block the current thread until all agents have finished.
        
        This method waits for all background thread agents to complete, and then
        forcibly shuts down the main thread agent if it exists and hasn't already
        been shut down.
        
        Returns:
            None
        """
        # Wait for all background thread agents to finish
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

        # Handle main thread agent if it exists
        if self.mainAgent is not None:
            # Force shutdown if not already shut down
            if not self.mainAgent.hasShutdown:
                with self.mainAgent.getTimer().run("shutdown"):
                    self.Sentinel.info("Shutting agent down with sigint")
                self.mainAgent.forceShutdown()
            
            # Force close if not already closed
            if not self.mainAgent.hasClosed:
                self.Sentinel.info("Closing agent with sigint")
                with self.mainAgent.getTimer().run("cleanup"):
                    self.mainAgent.onClose()

            self.Sentinel.info("Main agent finished")

    def shutDownNow(self) -> None:
        """
        Shut down the thread pool executor immediately.
        
        This method blocks until the executor has terminated all threads. It cancels
        any pending futures, which may prevent some agents from cleaning up properly.
        Use this method only when immediate shutdown is required.
        
        Returns:
            None
        """
        self.__executor.shutdown(wait=True, cancel_futures=True)
