"""
Neo Module - Main system entry point and coordinator.

This module provides the Neo class, which serves as the main entry point and
coordinator for the Alt system. Neo initializes all core components, manages
the system lifecycle, and provides interfaces for starting agents and orders.

Neo is responsible for:
- Initializing all core operators (Config, Property, Time, Order, Agent, etc.)
- Setting up the Central coordination system
- Managing system shutdown and cleanup
- Providing interfaces for starting agents and orders
- Handling signal interrupts

Neo is the first component to be initialized in the Alt system and the last one
to be shut down. It ensures proper startup and cleanup of all resources.
"""

import logging
import os
import signal
import socket
import sys
import time
from typing import Callable
from JXTABLES.XTablesClient import XTablesClient
from Core.TimeOperator import TimeOperator
from Core.ConfigOperator import ConfigOperator
from Core.PropertyOperator import PropertyOperator, LambdaHandler, ReadonlyProperty
from Core.OrderOperator import OrderOperator
from Core.AgentOperator import AgentOperator
from Core.ShareOperator import ShareOperator
from Core.XDashOperator import XDashOperator
from Core.UpdateOperator import UpdateOperator
from Core import LogManager, COREMODELTABLE, COREINFERENCEMODE
from Core.Central import Central
from abstract.Agent import Agent
from abstract.Order import Order
from JXTABLES.TempConnectionManager import TempConnectionManager as tcm

from tools.Constants import InferenceMode


# Main logger for Neo module
Sentinel = LogManager.Sentinel


class Neo:
    """
    Main system entry point and coordinator for the Alt system.
    
    Neo initializes all core components, manages the system lifecycle, and
    provides interfaces for starting agents and orders. It is the central
    coordinator that ties together all subsystems and ensures proper
    initialization, execution, and cleanup.
    
    Neo is designed to be the first component initialized and the last one to
    shut down. It handles signal interrupts to ensure clean system shutdown
    even when terminated externally.
    
    Attributes:
        __configOp (ConfigOperator): Configuration management
        __xclient (XTablesClient): Network tables client for communication
        __propertyOp (PropertyOperator): Property management
        __timeOp (TimeOperator): Time and performance tracking
        __shareOp (ShareOperator): Shared object management
        __orderOp (OrderOperator): Order management and execution
        __agentOp (AgentOperator): Agent lifecycle management
        __central (Central): Central coordination system
        __xdOp (XDashOperator): XDash integration
        __updateOperators (list): List of update operators for agents
        __isShutdown (bool): Flag indicating if Neo has been shut down
        __logMap (dict): Map of log entries for agents
    """
    def __init__(self) -> None:
        """
        Initialize Neo and all its subsystems.
        
        This constructor initializes all core components of the Alt system in
        the correct order, sets up signal handlers for clean shutdown, and
        prepares the system for operation.
        
        The initialization sequence is:
        1. ConfigOperator - For configuration management
        2. XTablesClient - For network communication
        3. PropertyOperator - For property management
        4. TimeOperator - For timing and performance tracking
        5. ShareOperator - For shared object management
        6. OrderOperator - For order management and execution
        7. AgentOperator - For agent lifecycle management
        8. Central - For central coordination
        9. XDashOperator - For XDash integration
        """
        self.__printInit()
        Sentinel.info("Creating Config operator")
        Sentinel.info("Loading configs")
        self.__configOp = ConfigOperator()
        
        Sentinel.info("Creating XTables Client....")
        tcm.invalidate()
        self.__xclient = XTablesClient(debug_mode=True)
        self.__xclient.add_client_version_property("MATRIX-ALT-VISION")
        while not self.__xclient.get_socket_montior().is_connected("PUSH"):
            Sentinel.info("Waiting for xtables push socket connection....")
        Sentinel.info("Client created")
        
        Sentinel.info("Creating Property operator")
        self.__propertyOp = PropertyOperator(
            self.__xclient,
            configOp=self.__configOp,
            logger=Sentinel.getChild("Property_Operator"),
            basePrefix=LogManager.UniqueId,
        )
        
        Sentinel.info("Creating Time operator")
        self.__timeOp = TimeOperator(
            propertyOp=self.__propertyOp,
            logger=Sentinel.getChild("Time_Operator"),
        )
        
        Sentinel.info("Creating Share operator")
        self.__shareOp = ShareOperator(
            logger=Sentinel.getChild("Share_Operator"),
        )
        
        Sentinel.info("Creating Order operator")
        self.__orderOp = OrderOperator(
            self.__xclient,
            propertyOp=self.__propertyOp,
            logger=Sentinel.getChild("Order_Operator"),
        )
        
        Sentinel.info("Creating Agent operator")
        self.__agentOp = AgentOperator(
            propertyOp=self.__propertyOp,
            timeOp=self.__timeOp,
            logger=Sentinel.getChild("Agent_Operator"),
        )
        
        Sentinel.info("Creating Central")
        self.__central = Central(
            logger=Sentinel.getChild("Central_Processor"),
            configOp=self.__configOp,
            propertyOp=self.__propertyOp,
            inferenceMode=COREINFERENCEMODE,
        )
        
        Sentinel.info("Creating XDASH operator")
        self.__xdOp = XDashOperator(
            central=self.__central,
            xclient=self.__xclient,
            propertyOperator=self.__propertyOp,
            configOperator=self.__configOp,
            shareOperator=self.__shareOp,
            logger=Sentinel.getChild("XDASH_Operator"),
        )
        
        self.__updateOperators = []

        # Set up signal handlers for clean shutdown
        self.__isShutdown = False
        signal.signal(signal.SIGINT, handler=self.__handleArchitectKill)
        signal.signal(signal.SIGTERM, handler=self.__handleArchitectKill)

        # Initialize logging for agents
        self.__logMap = {}
        self.__getBasePrefix = lambda agentName: f"active_agents.{agentName}"

    def getCentral(self) -> Central:
        """
        Get the Central coordination system instance.
        
        Returns:
            Central: The Central coordination system instance
        """
        return self.__central

    def __handleArchitectKill(self, sig, frame) -> None:
        """
        Handle termination signals (SIGINT, SIGTERM).
        
        This method is called when the process receives a termination signal
        (e.g., Ctrl+C, kill command). It performs a clean shutdown of the system.
        
        Args:
            sig: The signal received
            frame: The current stack frame
        """
        Sentinel.info("The architect has caused our demise! Shutting down any agent")
        self.shutDown()
        os._exit(1)  # Force exit after clean shutdown

    def shutDown(self) -> None:
        """
        Shut down the Neo system and all its components.
        
        This method stops all agents, deregisters all properties and orders,
        and performs cleanup of resources. It ensures a clean shutdown of the
        system. If the system is already shut down, this method does nothing.
        """
        if not self.__isShutdown:
            self.__agentOp.stopPermanent()
            self.__printAndCleanup()
            self.__isShutdown = True
        else:
            Sentinel.debug("Already shut down")

    def addOrderTrigger(self, orderTriggerName: str, orderToRun: type[Order]) -> None:
        """
        Add a new order trigger to the system.
        
        This method creates an instance of the specified order class, injects
        the necessary dependencies, and registers it with the OrderOperator
        under the specified trigger name.
        
        Args:
            orderTriggerName: The name of the trigger that will activate the order
            orderToRun: The order class to instantiate and register
            
        Note:
            This method does nothing if Neo has already been shut down.
        """
        if not self.isShutdown():
            # Create the order instance
            order = orderToRun()
            
            # Set up child property operator and timer
            childPropOp = self.__propertyOp.getChild(order.getName())
            timer = self.__timeOp.getTimer(order.getName())
            
            # Inject dependencies
            order.inject(
                self.__central,
                self.__xclient,
                childPropOp,
                self.__configOp,
                self.__shareOp,
                timer,
            )
            
            # Register with the order operator
            self.__orderOp.createOrderTrigger(orderTriggerName, order)
        else:
            Sentinel.warning("Neo is already shutdown!")

    def __handleLog(
        self, logProperty: ReadonlyProperty, newLog: str, maxLogLength: int = 3
    ) -> None:
        """
        Handle agent log entries.
        
        This private method manages agent log entries, keeping a rolling window
        of the most recent log messages and updating the log property.
        
        Args:
            logProperty: The property to store the log messages
            newLog: The new log message to add
            maxLogLength: Maximum number of log messages to keep
        """
        table = logProperty.getTable()
        lastlogs = self.__logMap.get(table, [])

        # Add new log and keep only the most recent entries
        lastlogs.append(newLog)
        lastlogs = lastlogs[-maxLogLength:]

        # Update the log property with joined messages
        msg = " ".join(lastlogs)
        logProperty.set(msg)
        self.__logMap[table] = lastlogs

    def wakeAgent(self, agentClass: type[Agent], isMainThread=False) -> None:
        """
        Create and start an agent of the specified class.
        
        This method instantiates an agent of the specified class, injects
        all necessary dependencies, and starts it. The agent can be run in 
        the main thread or in a background thread.
        
        Args:
            agentClass: The agent class to instantiate and start
            isMainThread: If True, run the agent in the main thread (blocking);
                         if False, run in a background thread (non-blocking)
                         
        Note:
            If isMainThread=True, this method will block indefinitely until
            the agent completes or the system is shut down.
            
            This method does nothing if Neo has already been shut down.
        """
        if not self.isShutdown():
            # Create agent instance
            agent = agentClass()
            agentName = agent.getName()

            # Set up child property operator and update operator
            childPropertyOp = self.__propertyOp.getChild(
                f"{self.__getBasePrefix(agentName)}"
            )
            updateOperator = UpdateOperator(self.__xclient, childPropertyOp)
            self.__updateOperators.append(updateOperator)
            
            # Set up logging for the agent
            childLogger = Sentinel.getChild(f"{agentName}")
            logTable = f"{self.__getBasePrefix(agentName)}.log"
            logProperty = self.__propertyOp.createCustomReadOnlyProperty(
                logTable, "None..."
            )
            logLambda = lambda entry: self.__handleLog(logProperty, entry)
            lambda_handler = LambdaHandler(logLambda)
            formatter = logging.Formatter("%(levelname)s-%(name)s: %(message)s")
            lambda_handler.setFormatter(formatter)
            childLogger.addHandler(lambda_handler)

            # Get timer for the agent
            timer = self.__timeOp.getTimer(agent.getName())

            # Inject dependencies into the agent
            agent.inject(
                central=self.__central,
                xclient=self.__xclient,
                propertyOperator=childPropertyOp,
                configOperator=self.__configOp,
                shareOperator=self.__shareOp,
                updateOperator=updateOperator,
                logger=childLogger,
                timer=timer,
                isMainThread=isMainThread,
            )
            
            # Start the agent (either in a background thread or main thread)
            if not isMainThread:
                self.__agentOp.wakeAgent(agent)
            else:
                self.__agentOp.wakeAgentMain(agent)
        else:
            Sentinel.warning("Neo is already shutdown!")

    def startXDashLoop(self) -> None:
        """
        Start the XDash loop for continuous dashboard updates.
        
        This method starts an infinite loop that continually updates the XDash
        dashboard. It is meant to be run in the main thread after all agents
        have been started.
        
        Note:
            This method blocks indefinitely and should typically be the last
            method called in the main thread.
        """
        while True:
            self.__xdOp.run()
            time.sleep(0.001)  # 1ms sleep to prevent CPU hogging

    def __printAndCleanup(self) -> None:
        """
        Print shutdown message and perform cleanup.
        
        This private method is called during shutdown to print a shutdown
        message and perform cleanup of resources.
        """
        self.__printFinish()
        self.__cleanup()

    def waitForAgentsFinished(self) -> None:
        """
        Wait for all agents to finish.
        
        This method blocks the current thread until all agents have finished
        executing. It is useful for ensuring that all agents have completed
        their tasks before proceeding.
        
        Note:
            This method does nothing if Neo has already been shut down.
        """
        if not self.isShutdown():
            self.__agentOp.waitForAgentsToFinish()
        else:
            self.Sentinel.warning("Neo has already been shut down!")

    def setOnAgentFinished(self, runOnFinish: Callable[[], None]) -> None:
        """
        Set a callback to be run when an agent finishes.
        
        This method registers a callback function that will be called when
        the next agent to finish completes. The callback is only registered
        if Neo is still running.
        
        Args:
            runOnFinish: A callback function to run when an agent finishes
            
        Note:
            This method does nothing if Neo has already been shut down.
        """
        if not self.isShutdown():
            self.__agentOp.setOnAgentFinished(runOnFinish)
        else:
            self.Sentinel.warning("Neo has already been shut down!")

    def __cleanup(self) -> None:
        """
        Perform cleanup of resources.
        
        This private method is called during shutdown to clean up resources
        used by Neo and its components. It deregisters properties and orders,
        and shuts down the agent operator.
        """
        # XTables operations (need to be performed before XClient shutdown)
        Sentinel.info(f"Properties removed: {self.__propertyOp.deregisterAll()}")
        Sentinel.info(f"Orders removed: {self.__orderOp.deregister()}")
        
        # Deregister update operators
        for updateOp in self.__updateOperators:
            updateOp.deregister()
            
        # Stop and shut down the agent operator
        self.__agentOp.stopPermanent()
        self.__agentOp.shutDownNow()

        # XClient shutdown is not necessary according to comments
        # try:
        #     self.__xclient.shutdown()
        # except Exception as e:
        #     Sentinel.debug(f"This happens sometimes: {e}")

    def isShutdown(self) -> bool:
        """
        Check if Neo has been shut down.
        
        Returns:
            bool: True if Neo has been shut down, False otherwise
        """
        return self.__isShutdown

    def __printInit(self) -> None:
        """
        Print the initialization ASCII art banner.
        
        This private method is called during initialization to print an
        ASCII art banner to the log.
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
        Print the shutdown ASCII art banner.
        
        This private method is called during shutdown to print an ASCII art
        banner to the log, indicating that Neo has been shut down.
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
