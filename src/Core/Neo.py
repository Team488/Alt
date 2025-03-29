# Core process. Will always be the first thing to run. ALWAYS
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
from Core.StreamOperator import StreamOperator
from Core import LogManager, COREMODELTABLE, COREINFERENCEMODE
from Core.Central import Central
from abstract.Agent import Agent
from abstract.Order import Order
from JXTABLES.TempConnectionManager import TempConnectionManager as tcm
from multiprocessing import Manager
from tools.Constants import InferenceMode


Sentinel = LogManager.Sentinel


class Neo:
    def __init__(self) -> None:
        self.__printInit()
        Sentinel.info("Creating Multiprocessing Manager")
        self.__manager = Manager()

        # Sentinel.info("Creating Config operator")
        # Sentinel.info("Loading configs")
        # self.__configOp = ConfigOperator()

        Sentinel.info("Invalidate xtables cache...")
        tcm.invalidate()
        # Sentinel.info("Creating XTables Client....")
        # self.__xclient = XTablesClient(debug_mode=True)
        # self.__xclient.add_client_version_property("MATRIX-ALT-VISION")
        # while not self.__xclient.get_socket_montior().is_connected("PUSH"):
        #     Sentinel.info("Waiting for xtables push socket connection....")
        # Sentinel.info("Client created")

        # Sentinel.info("Creating Property operator")
        # self.__propertyOp = PropertyOperator(
        #     self.__xclient,
        #     configOp=self.__configOp,
        # )
        # Sentinel.info("Creating Time operator")
        # self.__timeOp = TimeOperator(
        #     propertyOp=self.__propertyOp,
        # )

        Sentinel.info("Creating Share operator")
        self.__shareOp = ShareOperator(
            dict=self.__manager.dict(),
        )

        Sentinel.info("Creating Stream Operator")
        self.__streamOp = StreamOperator(manager=self.__manager)
        self.__streamOp.start()

        # Sentinel.info("Creating Order operator")
        # self.__orderOp = OrderOperator(
        #     self.__xclient,
        #     propertyOp=self.__propertyOp,
        # )

        Sentinel.info("Creating Agent operator")
        self.__agentOp = AgentOperator(self.__manager, self.__shareOp, self.__streamOp)

        self.__isShutdown = False  # runnable
        signal.signal(signal.SIGINT, handler=self.__handleArchitectKill)
        signal.signal(signal.SIGTERM, handler=self.__handleArchitectKill)

    def __handleArchitectKill(self, sig, frame) -> None:
        Sentinel.info("The architect has caused our demise! Shutting down any agent")
        self.shutDown()
        os._exit(1)

    def shutDown(self) -> None:
        if not self.__isShutdown:
            self.__agentOp.stopPermanent()
            self.__printAndCleanup()
            self.__isShutdown = True
        else:
            Sentinel.debug("Already shut down")

    def addOrderTrigger(self, orderTriggerName: str, orderToRun: type[Order]) -> None:
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
        """NOTE: if isMainThread=True, this will threadblock indefinitely"""
        if not self.isShutdown():
            self.__agentOp.wakeAgent(agentClass, isMainThread)
        else:
            Sentinel.warning("Neo is already shutdown!")

    def __printAndCleanup(self) -> None:
        self.__printFinish()
        self.__cleanup()

    def waitForAgentsFinished(self) -> None:
        """Thread blocking method that waits for a running agent (if any is running)"""
        if not self.isShutdown():
            self.__agentOp.waitForAgentsToFinish()
        else:
            self.Sentinel.warning("Neo has already been shut down!")

    def __cleanup(self) -> None:
        self.__streamOp.shutdown()
        self.__agentOp.waitForAgentsToFinish()
        self.__agentOp.shutDownNow()

    def isShutdown(self) -> bool:
        return self.__isShutdown

    def __printInit(self) -> None:
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
