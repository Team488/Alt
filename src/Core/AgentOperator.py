import ctypes
from functools import partial
import logging
import multiprocessing
import multiprocessing.context
import multiprocessing.managers
import multiprocessing.sharedctypes
import multiprocessing.synchronize
import pickle
import sys
import os
import threading
import traceback
import time
from logging import Logger
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor, Future
from typing import Any, Dict, Optional, Callable, Set, Union, cast
from JXTABLES.XTablesClient import XTablesClient
from Core.ConfigOperator import ConfigOperator
from Core.ShareOperator import ShareOperator
from Core.StreamOperator import StreamOperator
from Core.TimeOperator import TimeOperator, Timer
from Core.UpdateOperator import UpdateOperator
from abstract.Agent import Agent
from Core.PropertyOperator import LambdaHandler, PropertyOperator, ReadonlyProperty
from Core import LogManager
from Core import getChildLogger
from tools.AgentConstants import AgentCapabilites

Sentinel = getChildLogger("Agent_Operator")

# subscribes to command request with xtables and then executes when requested
class AgentOperator:
    def __init__(
        self,
        manager: multiprocessing.managers.SyncManager,
        shareOp: ShareOperator,
        streamOp: StreamOperator,
    ) -> None:
        self.__executor: ProcessPoolExecutor = ProcessPoolExecutor()
        self.__stop: threading.Event = manager.Event()  # flag
        self.futures: list[Future] = []
        self.activeAgentNames = {}
        self.mainAgent: Optional[Agent] = None
        self.shareOp = shareOp
        self.streamOp = streamOp
        self.manager = manager

    def __setStop(self, stop: bool):
        if stop:
            self.__stop.set()
        else:
            self.__stop.clear()

    def stopAndWait(self) -> None:
        """Stop all agents but allow them to clean up, and wait for them to finish"""
        self.__setStop(True)
        self.waitForAgentsToFinish()
        self.__setStop(False)

    def stopPermanent(self) -> None:
        """Set the stop flag permanently (will not be reset)"""
        self.__setStop(True)

    def __setMainAgent(self, agent: Agent):
        self.mainAgent = agent

    def getUniqueAgentName(self, agentClass: Union[partial, type[Agent]]):
        """Handles duplicate agent names"""
        if isinstance(agentClass, partial):
            name = agentClass.func.__name__
        else:
            name = agentClass.__name__

        currentRunningWithThatName = self.activeAgentNames.get(name, 0)

        if currentRunningWithThatName > 0:
            # already existing instances, so add a differentiator
            name = f"{name}_{currentRunningWithThatName}"

        currentRunningWithThatName += 1
        self.activeAgentNames[name] = currentRunningWithThatName

        return name

    def initalizeExtraObjects(
        self,
        agentClass: Union[partial, type[Agent]],
        agentName: str,
        argumentDict: multiprocessing.managers.DictProxy,
        streamOperator: StreamOperator,
    ):
        for capability in AgentCapabilites.getCapabilites(agentClass):
            # TODO add more
            if capability is AgentCapabilites.STREAM:
                argumentDict[
                    AgentCapabilites.STREAM.objectName
                ] = streamOperator.register_stream(agentName)

        return argumentDict

    def wakeAgent(self, agentClass: type[Agent], isMainThread: bool) -> None:
        Sentinel.info(f"Waking agent!")

        agentName = self.getUniqueAgentName(agentClass)

        extraObjects = self.initalizeExtraObjects(
            agentClass, agentName, self.manager.dict(), self.streamOp
        )

        if isMainThread:
            AgentOperator._startAgentLoop(
                agentClass,
                agentName,
                self.shareOp,
                True,
                self.__stop,
                extraObjects,
                runOnCreate=self.__setMainAgent,
            )
        else:
            # set new logger before fork
            # if isinstance(agentClass, partial):
            #     name = agentClass.func.__name__
            # else:
            #     name = agentClass.__name__
            # LogManager.createAndSetMain(name)

            try:
                self.futures.append(
                    self.__executor.submit(
                        AgentOperator._startAgentLoop,
                        agentClass,
                        agentName,
                        self.shareOp,
                        isMainThread,
                        self.__stop,
                        extraObjects,
                    )
                )
            except Exception as e:
                print(e)
            finally:
                # go back to core logger
                # LogManager.initMainLogger()
                pass

        Sentinel.info("The agent is alive!")

    @staticmethod
    def _handleLog(
        logProperty: ReadonlyProperty,
        lastLogs: list,
        newLog: str,
        maxLogLength: int = 3,
    ) -> None:

        lastLogs.append(newLog)
        lastLogs = lastLogs[-maxLogLength:]

        msg = " ".join(lastLogs)
        logProperty.set(msg)

    @staticmethod
    def _injectAgent(
        agent: Agent,
        agentName,
        shareOperator: ShareOperator,
        extraObjects: multiprocessing.managers.DictProxy,
        isMainThread: bool,
    ) -> Agent:

        # injecting stuff shared from core
        agent._injectCore(shareOperator, isMainThread, agentName)
        # creating new operators just for this agent and injecting them
        AgentOperator._injectNewOperators(agent, agentName)

        agent._setExtraObjects(extraObjects)

        # setup a log handler to go on xtables
        logTable = f"{agent.propertyOperator.getFullPrefix()}.log"
        logProperty = agent.propertyOperator.createCustomReadOnlyProperty(
            logTable, "None...", addBasePrefix=False, addOperatorPrefix=False
        )
        lastLogs = []

        logLambda = lambda entry: AgentOperator._handleLog(logProperty, lastLogs, entry)
        lambda_handler = LambdaHandler(logLambda)
        formatter = logging.Formatter("%(levelname)s-%(name)s: %(message)s")
        lambda_handler.setFormatter(formatter)
        agent.Sentinel.addHandler(lambda_handler)

        return agent

    @staticmethod
    def _injectNewOperators(agent: Agent, agentName):
        """Since any agent not on main thread will be in its own process, alot of new objects will have to be created"""
        client = XTablesClient()  # one per process
        configOp = (
            ConfigOperator()
        )  # TODO this might not be 100% necessary to be one per process
        propertyOp = PropertyOperator(client, configOp, prefix=agentName)
        updateOp = UpdateOperator(client, propertyOp)
        timeOp = TimeOperator(propertyOp)
        logger = getChildLogger(agentName)

        agent._injectNEW(
            xclient=client,
            propertyOperator=propertyOp,
            configOperator=configOp,
            updateOperator=updateOp,
            timeOperator=timeOp,
            logger=logger,
        )

    @staticmethod
    def _startAgentLoop(
        agentClass: type[Agent],
        agentName: str,
        shareOperator: ShareOperator,
        isMainThread: bool,
        stopflag: threading.Event,
        extraObjects: multiprocessing.managers.DictProxy,
        runOnCreate: Callable[[Agent], None] = None,
    ) -> None:
        """Main agent loop that manages agent lifecycle"""

        """Initialization part #1 Create agent"""
        agent: Agent = agentClass()
        capabilitesStr = [
            capability.name
            for capability in AgentCapabilites.getCapabilites(agentClass)
        ]

        """ Initialization part #3. Inject objects in agent"""
        AgentOperator._injectAgent(
            agent, agentName, shareOperator, extraObjects, isMainThread
        )

        """ On main thread this is how its set as main agent"""
        if isMainThread and runOnCreate is not None:
            runOnCreate(agent)

        # helper lambdas
        __setStatus: Callable[
            [str, str], bool
        ] = lambda status: agent.propertyOperator.createCustomReadOnlyProperty(
            f"{agentName}.Status", status
        ).set(
            status
        )
        __setErrorLog: Callable[
            [str, str], bool
        ] = lambda error: agent.propertyOperator.createCustomReadOnlyProperty(
            f"{agentName}.Errors", error
        ).set(
            error
        )
        __setDescription: Callable[
            [str, str], bool
        ] = lambda description: agent.propertyOperator.createCustomReadOnlyProperty(
            f"{agentName}.Description", description
        ).set(
            description
        )

        __setCapabilites: Callable[
            [str, str], bool
        ] = lambda capabilites: agent.propertyOperator.createCustomReadOnlyProperty(
            f"{agentName}.Capabilites", capabilites
        ).set(
            capabilites
        )

        def __handleException(exception: Exception) -> None:
            """Handle an exception that occurred during agent execution"""
            message: str = f"Failed! | During {progressStr}: {exception}"
            __setStatus(message)
            tb: str = traceback.format_exc()
            __setErrorLog(tb)
            Sentinel.error(tb)

        __setDescription(agent.getDescription())
        __setStatus("starting")
        __setCapabilites(capabilitesStr)

        # variables kept through agents life
        failed: bool = False
        progressStr: str = "starting"
        stop = False

        # use agents own timer
        timer: Timer = agent.getTimer()

        # start loop
        try:
            """Main part #1 Creation and running"""
            __setErrorLog("None...")

            # create
            progressStr = "create"
            __setStatus("creating")

            with timer.run("create"):
                agent.create()

            __setStatus("running")
            progressStr = "isRunning"
            while agent.isRunning():
                with timer.run("runPeriodic"):
                    stop = stopflag.is_set()
                    if stop:
                        break
                    progressStr = "runPeriodic"
                    agent.runPeriodic()

                    progressStr = "getIntervalMs"
                    intervalMs: int = agent.getIntervalMs()
                    if intervalMs > 0:
                        sleepTime: float = intervalMs / 1000  # ms -> seconds
                        time.sleep(sleepTime)

        except Exception as e:
            if type(e) is not KeyboardInterrupt:
                failed = True
                __handleException(e)

        finally:
            """Main part #2 possible shutdown"""
            # if thread was shutdown abruptly (self.__stop flag), perform shutdown
            # shutdown before onclose

            forceStopped: bool = stop
            if forceStopped:
                progressStr = "shutdown interrupt"
                __setStatus(progressStr)
                Sentinel.debug("Shutting down agent")
                try:
                    with timer.run("forceShutdown"):
                        agent.forceShutdown()
                        agent.hasShutdown = True
                except Exception as e:
                    failed = True
                    __handleException(e)

            elif not failed:
                __setStatus(f"agent isRunning returned false (Not an error)")
                Sentinel.debug(f"agent isRunning returned false (Not an error)")

            else:
                __setStatus(f"agent failed during {progressStr}")
                Sentinel.debug(f"agent failed during {progressStr}")

            """ Main part #3 Cleanup"""
            try:
                # cleanup
                with timer.run("onClose"):
                    agent.onClose()
                    agent.hasClosed = True

            except Exception as e:
                __handleException(e)

            agent._cleanup()  # shutdown new created objects in agent
            agent.isCleanedUp = True

    def allFinished(self):
        return all(f.done() for f in self.futures)

    def waitForAgentsToFinish(self) -> None:
        """Thread blocking method that waits for any running agents"""
        if not self.allFinished():
            Sentinel.info("Waiting for async agent to finish...")
            while True:
                # Sentinel.debug(f"waiting for futures: {self.futures}")
                if self.allFinished():
                    break
                time.sleep(0.01)
            Sentinel.info("Agents have all finished.")
        else:
            Sentinel.warning("No async agents to wait for!")

        if self.mainAgent is not None:
            if not self.mainAgent.hasShutdown:
                with self.mainAgent.getTimer().run("shutdown"):
                    Sentinel.info("Shutting agent down with sigint")
                    self.mainAgent.forceShutdown()
            if not self.mainAgent.hasClosed:
                Sentinel.info("Closing agent with sigint")
                with self.mainAgent.getTimer().run("cleanup"):
                    self.mainAgent.onClose()
            if not self.mainAgent.isCleanedUp:
                self.mainAgent._cleanup

            Sentinel.info("Main agent finished")

    def shutDownNow(self) -> None:
        """Threadblocks until executor is finished"""
        self.__executor.shutdown(wait=True, cancel_futures=True)
