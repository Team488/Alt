# Core process. Will always be the first thing to run. ALWAYS
import logging
import os
import signal
import socket
import sys
import time
from JXTABLES.XTablesClient import XTablesClient
from Core.ConfigOperator import ConfigOperator
from Core.PropertyOperator import PropertyOperator, LambdaHandler, ReadonlyProperty
from Core.OrderOperator import OrderOperator
from Core.AgentOperator import AgentOperator
from Core.ShareOperator import ShareOperator
from Core.XDashOperator import XDashOperator
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
        self.__xclient.add_client_version_property("MATRIX-ALT-VISION")
        Sentinel.info("Client created")
        Sentinel.info("Creating Property operator")
        self.__propertyOp = PropertyOperator(
            self.__xclient,
            configOp=self.__configOp,
            logger=Sentinel.getChild("Property_Operator"),
            basePrefix=UniqueId,
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
            logger=Sentinel.getChild("Agent_Operator"),
        )
        Sentinel.info("Creating Central")
        self.__central = Central(
            logger=Sentinel.getChild("Central_Processor"),
            configOp=self.__configOp,
            propertyOp=self.__propertyOp)
        Sentinel.info("Creating XDASH operator")
        self.__xdOp = XDashOperator(
            central=self.__central,
            xclient=self.__xclient,
            propertyOperator=self.__propertyOp,
            configOperator=self.__configOp,
            shareOperator=self.__shareOp,
            logger=Sentinel.getChild("XDASH_Operator"),
        )

        self.__isShutdown = False  # runnable
        signal.signal(signal.SIGINT, handler=self.__handleArchitectKill)
        signal.signal(signal.SIGTERM, handler=self.__handleArchitectKill)

        self.__logMap = {}
        self.__getBasePrefix = lambda agentName: f"active_agents.{agentName}"

    def __handleArchitectKill(self, sig, frame):
        Sentinel.info("The architect has caused our demise! Shutting down any agent")
        self.shutDown()
        os._exit(1)

    def shutDown(self):
        if not self.__isShutdown:
            self.__agentOp.stopPermanent()
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

    def __handleLog(
        self, logProperty: ReadonlyProperty, newLog: str, maxLogLength: int = 3
    ):
        table = logProperty.getTable()
        lastlogs = self.__logMap.get(table, [])

        lastlogs.append(newLog)
        lastlogs = lastlogs[-maxLogLength:]

        msg = " ".join(lastlogs)
        logProperty.set(msg)
        self.__logMap[table] = lastlogs

    def wakeAgentMain(self, agent: type[Agent], agentName=None):
        """NOTE: This will threadblock"""
        if not self.isShutdown():
            try:
                agentName = agent.getName()
            except Exception as e:
                Sentinel.debug(f"Error: {e}")

            if (
                agentName is None
            ):  # eg no backup name provided and cannot use agent.getName()
                Sentinel.warning(
                    "Since you are likely using a partial agent, you must provide an agent name separately!"
                )

            childPropertyOp = self.__propertyOp.getChild(
                f"{self.__getBasePrefix(agentName)}"
            )
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

            self.__agentOp.wakeAgentMain(
                agent(
                    central=self.__central,
                    xclient=self.__xclient,
                    propertyOperator=childPropertyOp,
                    configOperator=self.__configOp,
                    shareOperator=self.__shareOp,
                    logger=childLogger,
                )
            )
        else:
            Sentinel.warning("Neo is already shutdown!")

    def wakeAgent(self, agent: type[Agent]):
        if not self.isShutdown():
            try:
                agent.getName()
            except AttributeError as e:
                Sentinel.debug(e)
                Sentinel.fatal(
                    "If this agent is a partial agent, please use wakeAgentPartial!"
                )
                return
            self.wakeAgentPartial(agent, agent.getName())
        else:
            Sentinel.warning("Neo is already shutdown!")

    def wakeAgentPartial(self, agent: type[Agent], agentName):
        """This method is for agents that are created using functools partial\n
        For example the FrameProcessingAgentBase.PartialFrameProcessingAgent()\n
        NOTE: you must provide an agent name due to the how the functools partial works

        """
        if not self.isShutdown():
            childPropertyOp = self.__propertyOp.getChild(
                f"{self.__getBasePrefix(agentName)}"
            )
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

            self.__agentOp.wakeAgent(
                agent(
                    central=self.__central,
                    xclient=self.__xclient,
                    propertyOperator=childPropertyOp,
                    configOperator=self.__configOp,
                    shareOperator=self.__shareOp,
                    logger=childLogger,
                )
            )
        else:
            Sentinel.warning("Neo is already shutdown!")

    def startXDashLoop(self):
        while True:
            self.__xdOp.run()
            time.sleep(0.001)  # 1ms

    def __printAndCleanup(self):
        self.__printFinish()
        self.__cleanup()

    def waitForAgentsFinished(self):
        """Thread blocking method that waits for a running agent (if any is running)"""
        if not self.isShutdown():
            self.__agentOp.waitForAgentsToFinish()
        else:
            self.Sentinel.warning("Neo has already been shut down!")

    def setOnAgentFinished(self, runOnFinish):
        if not self.isShutdown():
            self.__agentOp.setOnAgentFinished(runOnFinish)
        else:
            self.Sentinel.warning("Neo has already been shut down!")

    def shutDownOnAgentsFinished(self):
        self.setOnAgentFinished(self.__printAndCleanup)

    def __cleanup(self):
        # xtables operations. need to go before xclient shutdown
        Sentinel.info(f"Properties removed: {self.__propertyOp.deregisterAll()}")
        Sentinel.info(f"Orders removed: {self.__orderOp.deregister()}")
        self.__agentOp.stopPermanent()
        self.__agentOp.shutDownNow()

        """ Xclient shutdown is not necessary <- from kobe"""
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
