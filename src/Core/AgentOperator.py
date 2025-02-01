import sys
import os
import threading
import traceback
import time
from logging import Logger
from JXTABLES.XTablesClient import XTablesClient
from abstract.Agent import Agent
from Core.PropertyOperator import PropertyOperator


# subscribes to command request with xtables and then executes when requested
class AgentOperator:
    def __init__(
        self, xclient: XTablesClient, logger: Logger, propertyOp: PropertyOperator
    ):
        self.Sentinel = logger
        self.propertyOp = propertyOp
        self.__xclient: XTablesClient = xclient
        self.__agentThread = None  # thread to run it
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

    def stop(self):
        self.__stop = True

    def join(self):
        if self.__agentThread is not None:
            self.__agentThread.join()
        else:
            self.Sentinel.warning("No agent thread to join!")

    def wakeAgent(self, agent: Agent):
        self.__stop = False  # reset stop flag (even if already false)

        if self.__agentThread is None:
            self.Sentinel.info(
                f"Waking agent! | Name: {agent.getName()} Description : {agent.getDescription()}"
            )
            self.__setDescription(agent.getName(), agent.getDescription())
            self.__setStatus(agent.getName(), "starting")
            self.__setStatus(agent.getName(), "starting2")
            self.__agentThread = threading.Thread(
                target=self.__startAgentLoop, args=[agent]
            )
            self.__agentThread.start()
            # grace period for thread to start
            while not self.__agentThread.is_alive():
                time.sleep(0.001)
            self.Sentinel.info("The agent is alive!")
        else:
            # agenthread already started
            self.Sentinel.warning("An agent has already been started!")

    def __startAgentLoop(self, agent: Agent):
        try:
            self.__setErrorLog(agent.getName(), "None...")
            # create
            progressStr = "create"
            self.__setStatus(agent.getName(), "creating")
            agent.create()

            self.__setStatus(agent.getName(), "running")
            progressStr = "isRunning"
            while agent.isRunning():
                if self.__stop:
                    break
                progressStr = "runPeriodic"
                agent.runPeriodic()

                progressStr = "getIntervalMs"
                intervalMs = agent.getIntervalMs()
                if intervalMs <= 0:
                    continue
                sleepTime = intervalMs / 1000  # ms -> seconds

                startTime = time.monotonic()
                while time.monotonic() - startTime < sleepTime:
                    time.sleep(0.001)  # Check every 1 ms

            # if thread was shutdown abruptly (self.__stop flag), perform shutdown
            # shutdown before onclose
            forceStopped = self.__stop
            if forceStopped:
                progressStr = "shutdown SIGINT"
                self.__setStatus(agent.getName(), progressStr)
                self.Sentinel.debug("Shutting down agent")
                agent.forceShutdown()
            else:
                progressStr = "close"
                self.__setStatus(agent.getName(), f"closing")
            # cleanup
            agent.onClose()

            if not forceStopped:
                self.__setStatus(
                    agent.getName(), f"agent isRunning returned false (Not an error)"
                )
                self.Sentinel.debug(f"agent isRunning returned false (Not an error)")

        except Exception as e:
            message = f"Failed! | During {progressStr}: {e}"
            self.__setStatus(agent.getName(), message)
            tb = traceback.format_exc()
            self.__setErrorLog(agent.getName(), tb)
            self.Sentinel.error(tb)

        # potentially run a task on agent finish
        if not self.__stop and self.__runOnFinish is not None:
            self.__runOnFinish()
            # clear
            self.__runOnFinish = None

        # end agent thread
        self.__agentThread = None

    def setOnAgentFinished(self, runOnFinish):
        if self.__agentThread is not None:
            self.__runOnFinish = runOnFinish
        else:
            self.Sentinel.warning("Neo is not alive yet!")

    def waitForAgentFinished(self):
        """Thread blocking method that waits for a running agent (if any is running)"""
        self.Sentinel.info("Waiting for agent to finish...")
        while self.__agentThread is not None and self.__agentThread.is_alive():
            time.sleep(0.001)
        else:
            self.Sentinel.info("Agent has finished.")
