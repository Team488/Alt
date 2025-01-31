# Core process. Will always be the first thing to run. ALWAYS
import logging
import os
import signal
import socket
import sys
import time
from JXTABLES.XTablesClient import XTablesClient
from Core.ConfigOperator import ConfigOperator
from Core.PropertyOperator import PropertyOperator
from Core.OrderOperator import OrderOperator
from Core.AgentOperator import AgentOperator
from Core.Central import Central
from abstract.Agent import Agent
from abstract.Order import Order

UniqueId = socket.gethostname()
Sentinel = logging.getLogger(f"Core[{UniqueId}]")
Sentinel.setLevel(level=logging.DEBUG)


class Neo:
    def __init__(self):
        self.__printInit()
        Sentinel.info("Creating Config operator")
        Sentinel.info("Loading configs")
        self.__configOp = ConfigOperator(logger=Sentinel.getChild("Config_Operator"))
        Sentinel.info("Creating XTables Client....")
        self.__xclient = XTablesClient(debug_mode=True)
        Sentinel.info("Client created")
        Sentinel.info("Creating Property operator")
        self.__propertyOp = PropertyOperator(
            self.__xclient,
            logger=Sentinel.getChild("Property_Operator"),
            prefix=UniqueId,
        )
        Sentinel.info("Creating Order operator")
        self.__orderOp = OrderOperator(
            self.__xclient,
            logger=Sentinel.getChild("Order_Operator"),
            propertyOp=self.__propertyOp,
        )
        Sentinel.info("Creating Agent operator")
        self.__agentOp = AgentOperator(
            self.__xclient,
            logger=Sentinel.getChild("Agent_Operator"),
            propertyOp=self.__propertyOp,
        )
        Sentinel.info("Creating Central")
        self.__central = Central(logger=Sentinel.getChild("Central_Processor"))

        self.__isShutdown = False  # runnable
        signal.signal(signal.SIGINT, handler=self.__handleArchitectKill)

    def __handleArchitectKill(self, sig, frame):
        Sentinel.info("The architect has caused our demise! Shutting down any agent")
        self.shutDown()
        os._exit(1)

    def shutDown(self):
        if not self.__isShutdown:
            self.__agentOp.stop()
            self.__agentOp.join()
            self.__printAndCleanup()
            self.__isShutdown = True
        else:
            Sentinel.debug("Already shut down")

    def addOrderTrigger(self, orderTriggerName: str, orderToRun: type[Order]):
        if not self.isShutdown():
            self.__orderOp.createOrderTrigger(
                orderTriggerName,
                orderToRun(
                    self.__central, self.__xclient, self.__propertyOp, self.__configOp
                ),
            )
        else:
            Sentinel.warning("Neo is already shutdown!")

    def wakeAgent(self, agent: type[Agent]):
        if not self.isShutdown():
            self.__agentOp.wakeAgent(
                agent(
                    self.__central,
                    self.__xclient,
                    self.__propertyOp,
                    self.__configOp,
                    Sentinel.getChild("Agent"),
                )
            )
        else:
            Sentinel.warning("Neo is already shutdown!")

    def __printAndCleanup(self):
        self.__printFinish()
        self.__cleanup()

    def waitForAgentFinished(self):
        """Thread blocking method that waits for a running agent (if any is running)"""
        if not self.isShutdown():
            self.__agentOp.waitForAgentFinished()
        else:
            self.Sentinel.warning("Neo has already been shut down!")

    def setOnAgentFinished(self, runOnFinish):
        if not self.isShutdown():
            self.__agentOp.setOnAgentFinished(runOnFinish)
        else:
            self.Sentinel.warning("Neo has already been shut down!")

    def shutDownOnAgentFinished(self):
        self.setOnAgentFinished(self.__printAndCleanup)

    def __cleanup(self):
        # xtables operations. need to go before xclient shutdown
        Sentinel.info(f"Properties removed: {self.__propertyOp.deregisterAll()}")
        Sentinel.info(f"Orders removed: {self.__orderOp.deregister()}")

        # try:
        #     self.__xclient.shutdown()
        # except Exception as e:
        #     Sentinel.debug(f"This happens sometimes: {e}")

    def isShutdown(self) -> bool:
        return self.__isShutdown

    def __printInit(self):
        message = """ /$$$$$$$$ /$$   /$$ /$$$$$$$$       /$$      /$$  /$$$$$$  /$$$$$$$$ /$$$$$$$  /$$$$$$ /$$   /$$
|__  $$__/| $$  | $$| $$_____/      | $$$    /$$$ /$$__  $$|__  $$__/| $$__  $$|_  $$_/| $$  / $$
   | $$   | $$  | $$| $$            | $$$$  /$$$$| $$  \ $$   | $$   | $$  \ $$  | $$  |  $$/ $$/
   | $$   | $$$$$$$$| $$$$$         | $$ $$/$$ $$| $$$$$$$$   | $$   | $$$$$$$/  | $$   \  $$$$/
   | $$   | $$__  $$| $$__/         | $$  $$$| $$| $$__  $$   | $$   | $$__  $$  | $$    >$$  $$
   | $$   | $$  | $$| $$            | $$\  $ | $$| $$  | $$   | $$   | $$  \ $$  | $$   /$$/\  $$
   | $$   | $$  | $$| $$$$$$$$      | $$ \/  | $$| $$  | $$   | $$   | $$  | $$ /$$$$$$| $$  \ $$
   |__/   |__/  |__/|________/      |__/     |__/|__/  |__/   |__/   |__/  |__/|______/|__/  |__/



 /$$    /$$                              /$$                                /$$$$$$  /$$    /$$$$$$$$
| $$   | $$                             |__/                               /$$__  $$| $$   |__  $$__/
| $$   | $$ /$$$$$$   /$$$$$$   /$$$$$$$ /$$  /$$$$$$  /$$$$$$$  /$$      | $$  \ $$| $$      | $$
|  $$ / $$//$$__  $$ /$$__  $$ /$$_____/| $$ /$$__  $$| $$__  $$|__/      | $$$$$$$$| $$      | $$
 \  $$ $$/| $$$$$$$$| $$  \__/|  $$$$$$ | $$| $$  \ $$| $$  \ $$          | $$__  $$| $$      | $$
  \  $$$/ | $$_____/| $$       \____  $$| $$| $$  | $$| $$  | $$ /$$      | $$  | $$| $$      | $$
   \  $/  |  $$$$$$$| $$       /$$$$$$$/| $$|  $$$$$$/| $$  | $$|__/      | $$  | $$| $$$$$$$$| $$
    \_/    \_______/|__/      |_______/ |__/ \______/ |__/  |__/          |__/  |__/|________/|__/



  /$$$$$$  /$$     /$$ /$$$$$$  /$$$$$$$$ /$$$$$$$$ /$$      /$$              /$$$$$$  /$$   /$$ /$$       /$$$$$$ /$$   /$$ /$$$$$$$$
 /$$__  $$|  $$   /$$//$$__  $$|__  $$__/| $$_____/| $$$    /$$$             /$$__  $$| $$$ | $$| $$      |_  $$_/| $$$ | $$| $$_____/
| $$  \__/ \  $$ /$$/| $$  \__/   | $$   | $$      | $$$$  /$$$$            | $$  \ $$| $$$$| $$| $$        | $$  | $$$$| $$| $$
|  $$$$$$   \  $$$$/ |  $$$$$$    | $$   | $$$$$   | $$ $$/$$ $$            | $$  | $$| $$ $$ $$| $$        | $$  | $$ $$ $$| $$$$$
 \____  $$   \  $$/   \____  $$   | $$   | $$__/   | $$  $$$| $$            | $$  | $$| $$  $$$$| $$        | $$  | $$  $$$$| $$__/
 /$$  \ $$    | $$    /$$  \ $$   | $$   | $$      | $$\  $ | $$            | $$  | $$| $$\  $$$| $$        | $$  | $$\  $$$| $$
|  $$$$$$/    | $$   |  $$$$$$/   | $$   | $$$$$$$$| $$ \/  | $$            |  $$$$$$/| $$ \  $$| $$$$$$$$ /$$$$$$| $$ \  $$| $$$$$$$$
 \______/     |__/    \______/    |__/   |________/|__/     |__/             \______/ |__/  \__/|________/|______/|__/  \__/|________/



 /$$$$$$$$ /$$      /$$         /$$    /$$$$$$   /$$$$$$   /$$$$$$
|__  $$__/| $$$    /$$$       /$$$$   /$$__  $$ /$$__  $$ /$$__  $$
   | $$   | $$$$  /$$$$      |_  $$  | $$  \ $$| $$  \ $$| $$  \ $$
   | $$   | $$ $$/$$ $$        | $$  |  $$$$$$$|  $$$$$$$|  $$$$$$$
   | $$   | $$  $$$| $$        | $$   \____  $$ \____  $$ \____  $$
   | $$   | $$\  $ | $$        | $$   /$$  \ $$ /$$  \ $$ /$$  \ $$
   | $$   | $$ \/  | $$       /$$$$$$|  $$$$$$/|  $$$$$$/|  $$$$$$/
   |__/   |__/     |__/      |______/ \______/  \______/  \______/"""
        Sentinel.info(f"\n\n{message}\n\n")

    def __printFinish(self):
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
