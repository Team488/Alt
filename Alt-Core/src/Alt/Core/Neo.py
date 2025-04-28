"""
core_matrix.py - The Matrix-Inspired Core Process Manager.

This file is the core entry point and orchestrator for the system, inspired by the Matrix universe.
It defines the `Neo` class, which acts as "The One" to bootstrap, manage, and gracefully shut down
all major operators and subsystems—such as agents, servers, streams, and shared state—using a combination
of multiprocessing, Flask-based services, and custom operators. Shutdown signals are intercepted and
handled with themed messaging, referencing the iconic Matrix architect. The overall design, naming,
and shutdown messages reflect a playful Matrix theme, while providing reliable infrastructure and process
management for the entire application.
"""

import os
import signal
from multiprocessing import Manager
from JXTABLES.TempConnectionManager import TempConnectionManager as tcm
from .Operators.FlaskOperator import FlaskOperator
from .Operators.AgentOperator import AgentOperator
from .Operators.ShareOperator import ShareOperator
from .Operators.StreamOperator import StreamOperator
from .Operators.LogStreamOperator import LogStreamOperator
from .Operators import LogOperator
from .Agents.Agent import Agent
from .Orders.Order import Order

Sentinel = LogOperator.Sentinel


class Neo:
    """
    The Matrix-inspired core process orchestration class.

    Neo is the central orchestrator and coordinator of all core operators and services.
    Channeling "The One" from the Matrix, this class bootstraps and manages the lifecycles
    of Flask servers, agent operators, share operators, streams, and dashboards.

    It handles system signals for graceful shutdown and wraps all initializations in
    Matrix-themed logging. Neo ensures reliable startup, monitoring, and teardown of all
    running processes. Key responsibilities include agent management, order triggers,
    dashboard launching, and robust process cleanup.

    Attributes:
        __manager (multiprocessing.Manager): Multiprocessing manager for shared objects.
        __shareOp (ShareOperator): Operator managing shared state between processes.
        __flaskOp (FlaskOperator): Runs the Flask-based API server.
        __streamOp (StreamOperator): Handles generic stream operations.
        __logStreamOp (LogStreamOperator): Manages log streams.
        __agentOp (AgentOperator): Boots and monitors Matrix agents.
        __isShutdown (bool): Tracks whether Neo has shut down.
        __isDashboardRunning (bool): Indicates if the dashboard is running.
    """

    def __init__(self) -> None:
        """
        Initializes the Neo orchestrator, setting up all core operators, intercepting shutdown
        signals, and starting the Flask server and other services.

        Raises:
            Exception: If any operator fails to initialize.
        """
        self.__printInit()
        Sentinel.info("Creating Multiprocessing Manager")
        self.__manager = Manager()
        Sentinel.info("Invalidate xtables cache...")
        tcm.invalidate()
        Sentinel.info("Creating Share operator")
        self.__shareOp = ShareOperator(
            dict=self.__manager.dict(),
        )
        Sentinel.info("Creating flask server")
        self.__flaskOp = FlaskOperator()
        Sentinel.info("Starting flask server")
        self.__flaskOp.start()
        Sentinel.info("Creating Stream Operator")
        self.__streamOp = StreamOperator(app=self.__flaskOp.getApp(), manager=self.__manager)
        Sentinel.info("Creating log stream operator")
        self.__logStreamOp = LogStreamOperator(app=self.__flaskOp.getApp(), manager=self.__manager)
        Sentinel.info("Creating Agent operator")
        self.__agentOp = AgentOperator(self.__manager, self.__shareOp, self.__streamOp, self.__logStreamOp)
        self.__isShutdown = False
        self.__isDashboardRunning = False
        # intercept shutdown signals to handle abrupt cleanup
        signal.signal(signal.SIGINT, handler=self.__handleArchitectKill)
        signal.signal(signal.SIGTERM, handler=self.__handleArchitectKill)

    def __handleArchitectKill(self, sig, frame) -> None:
        """
        Handles abrupt kill signals (SIGINT, SIGTERM) by performing a graceful shutdown,
        with Matrix-themed logging. Exits the program after cleanup.

        Args:
            sig (int): The received signal number.
            frame (FrameType): Current stack frame (unused).
        """
        Sentinel.info("The architect has caused our demise! Shutting down any agent")
        self.shutDown()
        os._exit(1)

    def shutDown(self) -> None:
        """
        Gracefully shuts down all agents, operators, and managed resources if not already shut down.

        This method is idempotent and will only operate if the system is not already shut down.
        """
        if not self.__isShutdown:
            self.__printAndCleanup()
            self.__isShutdown = True
        else:
            Sentinel.debug("Already shut down")

    def addOrderTrigger(self, orderTriggerName: str, orderToRun: type[Order]) -> None:
        """
        Adds a new order trigger to the system, creating and injecting dependencies for the specified Order.

        Args:
            orderTriggerName (str): Name of the trigger to register.
            orderToRun (type[Order]): The class of the Order to instantiate and register.

        Returns:
            None
        """
        if not self.isShutdown():
            order = orderToRun()
            childPropOp = self.__propertyOp.getChild(order.getName())
            timer = self.__timeOp.getTimer(order.getName())
            order.inject(
                self.__xclient,
                childPropOp,
                self.__configOp,
                self.__shareOp,
                timer,
            )
            self.__orderOp.createOrderTrigger(orderTriggerName, order)
        else:
            Sentinel.warning("Neo is already shutdown!")

    def wakeAgent(self, agentClass: type[Agent], isMainThread=False) -> None:
        """
        Awakens and starts the specified agent.

        If `isMainThread` is True, this method will block indefinitely in the main thread.

        Args:
            agentClass (type[Agent]): The Agent class to instantiate and start.
            isMainThread (bool, optional): Whether to block the main thread while running the agent. Defaults to False.

        Returns:
            None
        """
        if not self.isShutdown():
            self.__agentOp.wakeAgent(agentClass, isMainThread)
        else:
            Sentinel.warning("Neo is already shutdown!")

    def waitForAgentsFinished(self) -> None:
        """
        Blocks execution until all running agents have finished.

        Can be used in scripts to ensure all agent processes have completed before continuing.

        Returns:
            None
        """
        if not self.isShutdown():
            self.__agentOp.waitForAgentsToFinish()
        else:
            self.Sentinel.warning("Neo has already been shut down!")

    def runDashboard(self) -> None:
        """
        Launches the admin dashboard in a separate process if not already running and if Neo is not shut down.

        Catches missing dependencies and logs an appropriate message if the dashboard package is not installed.

        Returns:
            None
        """
        if not self.isShutdown() and not self.__isDashboardRunning:
            self.__isDashboardRunning = True
            try:
                from Alt.Dashboard import dashboard
                dashboard.mainAsync()
            except ImportError:
                Sentinel.fatal("To run the dashboard you must first install the pip package!\nRun:\npip install Alt-Dashboard")
        else:
            Sentinel.debug("Dashboard already running or neo shutdown")

    def __printAndCleanup(self) -> None:
        """
        Logs shutdown artwork and calls the resource cleanup routine.

        Returns:
            None
        """
        self.__printFinish()
        self.__cleanup()

    def __cleanup(self) -> None:
        """
        Performs cleanup of all agents, streams, Flask server, and shared resources.

        Ensures all subprocesses are stopped and resources are released.

        Returns:
            None
        """
        self.__agentOp.stopPermanent()
        self.__streamOp.shutdown()
        self.__flaskOp.shutdown()
        self.__agentOp.waitForAgentsToFinish()
        self.__manager.shutdown()
        self.__agentOp.shutDownNow()

    def isShutdown(self) -> bool:
        """
        Checks whether the shutdown routine has been called on Neo.

        Returns:
            bool: True if Neo has been shut down, False otherwise.
        """
        return self.__isShutdown

    def __printInit(self) -> None:
        """
        Prints the Matrix-themed ASCII intro banner during system initialization.

        Returns:
            None
        """
        message = """ /$$$$$$$$ /$$   /$$ /$$$$$$$$       /$$      /$$  /$$$$$$  /$$$$$$$$ /$$$$$$$  /$$$$$$ /$$   /$$
|__  $$__/| $$  | $$| $$_____/      | $$$    /$$$ /$$__  $$|__  $$__/| $$__  $$|_  $$_/| $$  / $$
   | $$   | $$  | $$| $$            | $$$$  /$$$$| $$  \\ $$   | $$   | $$  \\ $$  | $$  |  $$/ $$/
   | $$   | $$$$$$$$| $$$$$         | $$ $$/$$ $$| $$$$$$$$   | $$   | $$$$$$$/  | $$   \\  $$$$/
   | $$   | $$__  $$| $$__/         | $$  $$$| $$| $$__  $$   | $$   | $$__  $$  | $$    >$$  $$
   | $$   | $$  | $$| $$            | $$\\  $ | $$| $$  | $$   | $$   | $$  \\ $$  | $$   /$$/\\  $$
   | $$   | $$  | $$| $$$$$$$$      | $$ \\/  | $$| $$  | $$   | $$   | $$  | $$ /$$$$$$| $$  \\ $$
   |__/   |__/  |__/|________/      |__/     |__/|__/  |__/   |__/   |__/  |__/|______/|__/  |__/



 /$$    /$$                              /$$                                /$$$$$$  /$$    /$$$$$$$$
| $$   | $$                             |__/                               /$$__  $$| $$   |__  $$__/
| $$   | $$ /$$$$$$   /$$$$$$   /$$$$$$$ /$$  /$$$$$$  /$$$$$$$  /$$      | $$  \\ $$| $$      | $$
|  $$ / $$//$$__  $$ /$$__  $$ /$$_____/| $$ /$$__  $$| $$__  $$|__/      | $$$$$$$$| $$      | $$
 \\  $$ $$/| $$$$$$$$| $$  \\__/|  $$$$$$ | $$| $$  \\ $$| $$  \\ $$          | $$__  $$| $$      | $$
  \\  $$$/ | $$_____/| $$       \\____  $$| $$| $$  | $$| $$  | $$ /$$      | $$  | $$| $$      | $$
   \\  $/  |  $$$$$$$| $$       /$$$$$$$/| $$|  $$$$$$/| $$  | $$|__/      | $$  | $$| $$$$$$$$| $$
    \\_/    \\_______/|__/      |_______/ |__/ \\______/ |__/  |__/          |__/  |__/|________/|__/



  /$$$$$$  /$$     /$$ /$$$$$$  /$$$$$$$$ /$$$$$$$$ /$$      /$$              /$$$$$$  /$$   /$$ /$$       /$$$$$$ /$$   /$$ /$$$$$$$$
 /$$__  $$|  $$   /$$//$$__  $$|__  $$__/| $$_____/| $$$    /$$$             /$$__  $$| $$$ | $$| $$      |_  $$_/| $$$ | $$| $$_____/
| $$  \\__/ \\  $$ /$$/| $$  \\__/   | $$   | $$      | $$$$  /$$$$            | $$  \\ $$| $$$$| $$| $$        | $$  | $$$$| $$| $$
|  $$$$$$   \\  $$$$/ |  $$$$$$    | $$   | $$$$$   | $$ $$/$$ $$            | $$  | $$| $$ $$ $$| $$        | $$  | $$ $$ $$| $$$$$
 \\____  $$   \\  $$/   \\____  $$   | $$   | $$__/   | $$  $$$| $$            | $$  | $$| $$  $$$$| $$        | $$  | $$  $$$$| $$__/
 /$$  \\ $$    | $$    /$$  \\ $$   | $$   | $$      | $$\\  $ | $$            | $$  | $$| $$\\  $$$| $$        | $$  | $$\\  $$$| $$
|  $$$$$$/    | $$   |  $$$$$$/   | $$   | $$$$$$$$| $$ \\/  | $$            |  $$$$$$/| $$ \\  $$| $$$$$$$$ /$$$$$$| $$ \\  $$| $$$$$$$$
 \\______/     |__/    \\______/    |__/   |________/|__/     |__/             \\______/ |__/  \\__/|________/|______/|__/  \\__/|________/



 /$$$$$$$$ /$$      /$$         /$$    /$$$$$$   /$$$$$$   /$$$$$$
|__  $$__/| $$$    /$$$       /$$$$   /$$__  $$ /$$__  $$ /$$__  $$
   | $$   | $$$$  /$$$$      |_  $$  | $$  \\ $$| $$  \\ $$| $$  \\ $$
   | $$   | $$ $$/$$ $$        | $$  |  $$$$$$$|  $$$$$$$|  $$$$$$$
   | $$   | $$  $$$| $$        | $$   \\____  $$ \\____  $$ \\____  $$
   | $$   | $$\\  $ | $$        | $$   /$$  \\ $$ /$$  \\ $$ /$$  \\ $$
   | $$   | $$ \\/  | $$       /$$$$$$|  $$$$$$/|  $$$$$$/|  $$$$$$/
   |__/   |__/     |__/      |______/ \\______/  \\______/  \\______/"""
        Sentinel.info(f"\n\n{message}\n\n")

    def __printFinish(self) -> None:
        """
        Prints the Matrix character Agent Smith ASCII outro banner during system shutdown.

        Returns:
            None
        """
        message = """⠀⠀⠀⠀⠀⠀⣀⣤⣴⣶⣶⣦⣤⡀⠀⠀⠀⠀⠀⠀⠀
⠀⠀⠀⢀⣴⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣦⣄⠀⠀⠀
⠀⠀⢀⣾⣿⣿⣿⠿⣿⣿⣿⣿⣿⣿⠿⣿⣿⣿⣷⡀⠀
⠀⠀⢸⣿⣿⠋⠀⠀⠸⠿⠿⠿⠿⠇⠀⠀⠙⢿⣿⡇⠀
⠀⠀⢸⣿⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠘⣿⡇⠀
⠀⠀⢸⣿⠠⣤⣄⣀⠀⠀⠀⠀⠀⠀⣀⣠⣤⠀⣿⡇⠀
⠀⠀⣸⣿⣠⣴⣿⣿⣿⣷⣄⣠⣾⣿⣿⣿⣦⣄⣿⣇⠀
⣠⣼⣿⣿⢹⣿⣿⣿⣿⡿⠉⠉⢿⣿⣿⣿⣿⡇⣿⣿⡇
⣿⣿⣿⣿⠀⠈⠉⠁⠀⠀⠀⠀⠀⠀⠉⠉⠁⠀⣿⣿⠇
⢸⡇⢹⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣿⡏⠀
⢸⡇⢸⣿⠀⠀⠀⠀⢠⣤⣶⣶⣦⡄⠀⠀⠀⠀⣿⡇⠀
⢸⡇⠘⢿⣷⣄⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣠⣾⡿⠃⠀
⢸⣇⠀⠈⢻⣿⣷⣤⡀⠀⠀⠀⠀⢀⣴⣾⣿⡏⠀⠀⠀
⠀⠻⢷⣦⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡄⠀⠀
⠀⠀⠀⠸⠿⠿⠿⠿⠿⠏⠀⠀⠙⠿⠿⠿⠿⠿⠇⠀⠀"""
        Sentinel.info(f"\nNeo has been shutdown.\nWatch Agent Smith...\n{message}")
