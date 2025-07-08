"""AgentOperator.py

This module defines the AgentOperator class, which manages the lifecycle and execution
of Agent instances, including their initialization, proxy setup, logging, and shutdown.
It provides mechanisms for running agents in separate processes or threads, handling
their status, and ensuring proper cleanup.

Classes:
    AgentOperator: Manages agent processes, proxies, and lifecycle events.

Functions:
    (All public and private methods of AgentOperator are documented at the class and function level.)
"""

from __future__ import annotations

import logging
import multiprocessing
import multiprocessing.managers
import queue
import signal
import threading
import traceback
import time
from functools import partial
from concurrent.futures import ProcessPoolExecutor, Future
from typing import Optional, Callable, Union

from JXTABLES.XTablesClient import XTablesClient

from .ConfigOperator import ConfigOperator
from .ShareOperator import ShareOperator
from .StreamOperator import StreamOperator
from .TimeOperator import TimeOperator, Timer
from .UpdateOperator import UpdateOperator
from .LogStreamOperator import LogStreamOperator
from ..Agents import Agent, BindableAgent, TAgent
from .PropertyOperator import LambdaHandler, PropertyOperator, ReadonlyProperty
from .LogOperator import getChildLogger
from ..Constants.AgentConstants import ProxyType

Sentinel = getChildLogger("Agent_Operator")


# subscribes to command request with xtables and then executes when requested
class AgentOperator:
    """
    Manages the lifecycle, execution, and communication of Agent instances.

    Responsibilities include:
    - Starting and stopping agents, both in the main thread and in subprocesses.
    - Handling agent proxies for inter-process communication.
    - Managing agent logging and status reporting.
    - Ensuring proper cleanup and shutdown of agents.
    """

    STATUS = "status"
    DESCRIPTION = "description"
    ERRORS = "errors"
    CAPABILITES = "capabilites"

    CREATETIMER = "create"
    PERIODICTIMER = "runPeriodic"
    SHUTDOWNTIMER = "shutdown"
    CLOSETIMER = "close"

    def __init__(
        self,
        manager: multiprocessing.managers.SyncManager,
        shareOp: ShareOperator,
        streamOp: StreamOperator,
        logStreamOp: LogStreamOperator,
    ) -> None:
        """
        Initializes the AgentOperator.

        Args:
            manager (multiprocessing.managers.SyncManager): Manager for shared objects.
            shareOp (ShareOperator): Operator for shared data.
            streamOp (StreamOperator): Operator for stream proxies.
            logStreamOp (LogStreamOperator): Operator for log stream proxies.
        """
        self.__executor: ProcessPoolExecutor = ProcessPoolExecutor()
        self.__stop: threading.Event = manager.Event()  # flag
        self.futures: list[Future] = []
        self.activeAgentNames: dict[str, int] = {}
        self.mainAgent: Optional[Agent] = None
        self.shareOp = shareOp
        self.streamOp = streamOp
        self.logStreamOp = logStreamOp
        self.manager = manager

    def __setStop(self, stop: bool):
        """
        Sets or clears the stop flag for agent execution.

        Args:
            stop (bool): If True, sets the stop flag; otherwise, clears it.
        """
        try:
            if stop:
                self.__stop.set()
            else:
                self.__stop.clear()
        except BrokenPipeError:
            pass

    def stopAndWait(self) -> None:
        """Stop all agents but allow them to clean up, and wait for them to finish."""
        self.__setStop(True)
        self.waitForAgentsToFinish()
        self.__setStop(False)

    def stopPermanent(self) -> None:
        """Set the stop flag permanently (will not be reset)."""
        self.__setStop(True)

    def __setMainAgent(self, agent: Agent):
        """
        Sets the main agent reference.

        Args:
            agent (Agent): The agent to set as the main agent.
        """
        self.mainAgent = agent

    def getUniqueAgentName(self, agentClass: Union[partial, type[Agent]]):
        """
        Generates a unique name for an agent, handling duplicates.

        Args:
            agentClass (Union[partial, type[Agent]]): The agent class or partial.

        Returns:
            str: A unique agent name.
        """
        if isinstance(agentClass, partial):
            name = agentClass.func.__name__
        else:
            name = agentClass.__name__

        currentRunningWithThatName = self.activeAgentNames.get(name, 0)

        if currentRunningWithThatName > 0:
            # already existing instances, so add a differentiator
            newName = f"{name}_{currentRunningWithThatName}"
        else:
            newName = name

        currentRunningWithThatName += 1
        self.activeAgentNames[name] = currentRunningWithThatName

        return newName

    def initalizeProxies(
        self,
        agentClass: Union[partial, type[Agent]],
        agentName: str,
        proxyDict: multiprocessing.managers.DictProxy,
    ) -> tuple[multiprocessing.managers.DictProxy, queue.Queue]:
        """
        Initializes proxies for the agent, including stream and log proxies.

        Args:
            agentClass (Union[partial, type[Agent]]): The agent class or partial.
            agentName (str): The unique agent name.
            proxyDict (multiprocessing.managers.DictProxy): The proxy dictionary.

        Returns:
            tuple: (proxyDict, logProxy)
        """
        for requestName, proxyType in ProxyType.getProxyRequests(agentClass).items():
            # TODO add more
            if proxyType is ProxyType.STREAM:
                proxyDict[requestName] = self.streamOp.register_stream(agentName)

        # always create log queue
        logProxy = self.logStreamOp.register_log_stream(agentName)

        return proxyDict, logProxy

    def wakeAgent(self, agentClass: type[Agent], isMainThread: bool) -> None:
        """
        Starts an agent, either in the main thread or in a subprocess.

        Args:
            agentClass (type[Agent]): The agent class to instantiate and run.
            isMainThread (bool): Whether to run in the main thread.
        """
        Sentinel.info(f"Waking agent!")

        agentName = self.getUniqueAgentName(agentClass)

        proxies, logProxy = self.initalizeProxies(
            agentClass, agentName, self.manager.dict()
        )

        if isMainThread:
            AgentOperator._startAgentLoop(
                agentClass,
                agentName,
                self.shareOp,
                True,
                self.__stop,
                proxies,
                logProxy,
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
                        proxies,
                        logProxy,
                    )
                )
            except Exception as e:
                Sentinel.fatal(e)
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
        """
        Handles log messages for an agent, maintaining a rolling window of recent logs.

        Args:
            logProperty (ReadonlyProperty): The property to update with log messages.
            lastLogs (list): The list of recent log messages.
            newLog (str): The new log message to add.
            maxLogLength (int): The maximum number of log messages to keep.
        """
        lastLogs.append(newLog)
        lastLogs = lastLogs[-maxLogLength:]

        msg = " ".join(lastLogs)
        logProperty.set(msg)

    @staticmethod
    def _injectAgent(
        agent: Agent,
        agentName,
        shareOperator: ShareOperator,
        proxies: multiprocessing.managers.DictProxy,
        logProxy: queue.Queue,
        isMainThread: bool,
    ) -> Agent:
        """
        Injects core dependencies and logging into the agent.

        Args:
            agent (Agent): The agent instance.
            agentName (str): The agent's unique name.
            shareOperator (ShareOperator): The shared operator.
            proxies (DictProxy): The proxy dictionary.
            logProxy (queue.Queue): The log proxy queue.
            isMainThread (bool): Whether running in the main thread.

        Returns:
            Agent: The injected agent.
        """
        assert agent is not None
        # injecting stuff shared from core
        agent._injectCore(shareOperator, isMainThread, agentName)
        # creating new operators just for this agent and injecting them
        AgentOperator._injectNewOperators(agent, agentName, logProxy)

        agent._setProxies(proxies)

        # setup a log handler to go on xtables
        logTable = f"{agent.propertyOperator.getFullPrefix()}.log"
        logProperty = agent.propertyOperator.createCustomReadOnlyProperty(
            logTable, "None...", addBasePrefix=False, addOperatorPrefix=False
        )
        lastLogs: list[str] = []

        logLambda = lambda entry: AgentOperator._handleLog(logProperty, lastLogs, entry)
        lambda_handler = LambdaHandler(logLambda)
        formatter = logging.Formatter("%(levelname)s-%(name)s: %(message)s")
        lambda_handler.setFormatter(formatter)
        agent.Sentinel.addHandler(lambda_handler)

        return agent

    @staticmethod
    def _injectNewOperators(
        agent: Agent, agentName: str, logProxy: queue.Queue
    ) -> None:
        """
        Injects new operator instances and logging handlers into the agent.

        Args:
            agent (Agent): The agent instance.
            agentName (str): The agent's unique name.
            logProxy (queue.Queue): The log proxy queue.
        """
        client = XTablesClient(debug_mode=True)  # one per process
        client.add_client_version_property(f"MATRIX-ALT-{agentName}")

        configOp = (
            ConfigOperator()
        )  # TODO this might not be 100% necessary to be one per process
        propertyOp = PropertyOperator(client, configOp, prefix=agentName)
        updateOp = UpdateOperator(client, propertyOp)
        timeOp = TimeOperator(propertyOp)
        logger = getChildLogger(agentName)

        # add sse handling automatically
        class SSELogHandler(logging.Handler):
            closed = False

            def emit(self, record):
                if not self.closed:
                    try:
                        log_entry = self.format(record)
                        logProxy.put(log_entry)
                    except BrokenPipeError:
                        self.closed = True

        sse_handler = SSELogHandler()
        sse_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")
        )

        logger.addHandler(sse_handler)

        assert agent is not None

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
        agentClass: type[TAgent],
        agentName: str,
        shareOperator: ShareOperator,
        isMainThread: bool,
        stopflag: threading.Event,
        proxies: multiprocessing.managers.DictProxy,
        logProxy: queue.Queue,
        runOnCreate: Optional[Callable[[Agent], None]] = None,
    ) -> None:
        """
        Main agent loop that manages agent lifecycle, including creation, running,
        shutdown, and cleanup.

        Args:
            agentClass (type[Agent]): The agent class to instantiate.
            agentName (str): The agent's unique name.
            shareOperator (ShareOperator): The shared operator.
            isMainThread (bool): Whether running in the main thread.
            stopflag (threading.Event): The stop flag event.
            proxies (DictProxy): The proxy dictionary.
            logProxy (queue.Queue): The log proxy queue.
            runOnCreate (Optional[Callable[[Agent], None]]): Optional callback to run on agent creation.
        """
        if not isMainThread:
            signal.signal(signal.SIGINT, signal.SIG_IGN)
            signal.signal(signal.SIGTERM, signal.SIG_IGN)
            # we use our own interrupts to stop the pool, so ignore signals from sigint

        """Main agent loop that manages agent lifecycle"""

        # variables kept through agents life
        failed: bool = False
        progressStr: str = "starting"
        stop = False

        """Initialization part #1 Create agent"""
        try:
            agent: Agent = agentClass()
        except TypeError as e:
            # constructor misssing arguments
            # three possible mistakes.
            # 1) agentClass forgot to implement the bindableAgent interface and call bind before with arguments
            # 2) agentClass implemented the bindableAgent interface, it was called, but the bind method didint bind ALL arguments
            # 3) agentClass was passed in rather than agentClass.bind(...), which would return a partial

            if isinstance(agentClass, partial):
                # bind method must have been called, thus it is case 2)
                raise RuntimeError(
                    f"The bind method of {agentClass} did not cover all arguments! It must cover EVERY argument in __init__() \n{e}"
                )
            else:
                if issubclass(agentClass, BindableAgent):
                    # bind method wasnt called, case 3
                    raise RuntimeError(
                        f"""{agentClass} is a bindable agent! You must called {agentClass}'s bind() method,\n
                                        provide arguments, and then pass in the returned object instead! \n{e}"""
                    )
                else:
                    # no bind method, but there should be, case 1
                    raise RuntimeError(
                        f"""{agentClass} needs input arguments!. You must implement the bindableAgent interface,\n
                                        override the bind() method with necessary arguments (same as __init__), then call bind() and pass in the returned object instead! \n{e}"""
                    )

        assert agent is not None

        # helper lambdas
        __setStatus: Callable[
            [str], bool
        ] = lambda status: agent.propertyOperator.createCustomReadOnlyProperty(
            f"{agentName}.{AgentOperator.STATUS}", status
        ).set(
            status
        )
        __setErrorLog: Callable[
            [str], bool
        ] = lambda error: agent.propertyOperator.createCustomReadOnlyProperty(
            f"{agentName}.{AgentOperator.ERRORS}", error
        ).set(
            error
        )
        __setDescription: Callable[
            [str], bool
        ] = lambda description: agent.propertyOperator.createCustomReadOnlyProperty(
            f"{agentName}.{AgentOperator.DESCRIPTION}", description
        ).set(
            description
        )

        def __handleException(exception: Exception) -> None:
            """Handle an exception that occurred during agent execution"""
            message: str = f"Failed! | During {progressStr}: {exception}"
            __setStatus(message)
            tb: str = traceback.format_exc()
            __setErrorLog(tb)
            Sentinel.error(tb)

        try:

            """Initialization part #3. Inject objects in agent"""
            AgentOperator._injectAgent(
                agent, agentName, shareOperator, proxies, logProxy, isMainThread
            )
            """ On main thread this is how its set as main agent"""
            if isMainThread and runOnCreate is not None:
                runOnCreate(agent)

        except Exception as e:
            __handleException(e)
            failed = True
            stop = True
            progressStr = "critical core agent code exception"
            # means a bug in the core agent initalization code

        __setDescription(agent.getDescription())
        __setStatus(progressStr)

        # use agents own timer
        timer: Timer = agent.getTimer()

        # start loop
        try:
            """Main part #1 Creation and running"""
            __setErrorLog("None...")

            # create
            progressStr = "create"
            __setStatus("creating")

            with timer.run(AgentOperator.CREATETIMER):
                agent._runOwnCreate()
                agent.create()

            __setStatus("running")
            progressStr = "isRunning"
            while agent.isRunning():
                with timer.run(AgentOperator.PERIODICTIMER):
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
                    with timer.run(AgentOperator.SHUTDOWNTIMER):
                        agent.forceShutdown()
                        agent.hasShutdown = True
                except Exception as e:
                    failed = True
                    __handleException(e)

            elif not failed:
                __setStatus(f"agent finished normally")
                Sentinel.debug(f"agent finished normally")

            else:
                __setStatus(f"agent failed during {progressStr}")
                Sentinel.debug(f"agent failed during {progressStr}")

            """ Main part #3 Cleanup"""
            try:
                # cleanup
                with timer.run(AgentOperator.CLOSETIMER):
                    agent.onClose()
                    agent.hasClosed = True

            except Exception as e:
                __handleException(e)

            agent._cleanup()  # shutdown new created objects in agent
            agent.isCleanedUp = True

    def allFinished(self):
        """
        Checks if all agent futures have completed.

        Returns:
            bool: True if all agents are finished, False otherwise.
        """
        return all(f.done() for f in self.futures)

    def waitForAgentsToFinish(self) -> None:
        """
        Thread blocking method that waits for any running agents to finish.
        Also ensures the main agent is properly shut down and cleaned up.
        """
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
                Sentinel.info("cleaning agent with sigint")
                self.mainAgent._cleanup()

            self.mainAgent.propertyOperator.createCustomReadOnlyProperty(
                f"{self.mainAgent.agentName}.{AgentOperator.STATUS}", ""
            ).set("shutdown interrupt")

            Sentinel.info("Main agent finished")

    def shutDownNow(self) -> None:
        """
        Blocks the thread until the executor is finished and all agent processes are shut down.
        """
        self.__executor.shutdown(wait=True, cancel_futures=True)
