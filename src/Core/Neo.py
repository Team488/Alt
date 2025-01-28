# Core process. Will always be the first thing to run. ALWAYS
import logging
import os
import signal
import sys
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from JXTABLES.XTablesClient import XTablesClient
from Core.ConfigOperator import ConfigOperator
from Core.PropertyOperator import PropertyOperator
from Core.Central import Central
from abstract.Agent import Agent

logging.basicConfig(level=logging.DEBUG)
Sentinel = logging.getLogger("Core")

class Neo:
    DEFAULT_LOOP_TIME = 0.001 # 1 ms
    def __init__(self):
        self.__printInit()
        Sentinel.info("Creating Config operator")
        Sentinel.info("Loading configs")
        self.__configOp = ConfigOperator()
        Sentinel.info("Creating XTables Client....")
        self.__xclient = XTablesClient()
        Sentinel.info("Client created")
        Sentinel.info("Creating Property operator")
        self.__propertyOp = PropertyOperator(self.__xclient)
        Sentinel.info("Creating Central")
        self.__central = Central()
        Sentinel.info("Creating Merovingian (ThreadPool)")
        self.__mero = ThreadPoolExecutor(max_workers=5)
        self.__agentFinishEvent = threading.Event()  # Event to signal when the agent is done
        self.__agentThread = None # thread to run it
        self.__stop = False # flag
        self.__runOnFinish = None # runnable
        self.__isShutdown = False # runnable
        signal.signal(signal.SIGINT,handler=self.handleArchitectKill)

    def handleArchitectKill(self, signal, frame):
        Sentinel.info("The architect has caused our demise! Shutting down any agents")
        self.__shutDownINT()

    def __shutDownINT(self):
        self.__printFinish()
        self.__cleanup()          
        self.__stop = True
    
    def wakeAgent(self, agent : type[Agent]):
        if not self.isShutdown():
          agent = agent(self.__central,self.__xclient,self.__propertyOp,self.__configOp)
          if self.__agentThread is None:
            Sentinel.info("Waking agent!")          
            self.__agentThread = threading.Thread(target=self.__startAgentLoop,args=[agent])
            self.__agentThread.start()
            # grace period for thread to start
            while not self.__agentThread.is_alive():
                time.sleep(0.001)
            Sentinel.info("The agent is alive!")
          else:
            # agenthread already started 
            Sentinel.warning("An agent has already been started!")
        else:
           Sentinel.warning("Cannot begin, Neo is shut down!")
    
    def __startAgentLoop(self, agent : Agent):
        # create
        agent.create()
        
        continue_condition = lambda : not self.__stop and agent.isRunning()
        while continue_condition():              
            agent.runPeriodic()

            sleepTime = self.DEFAULT_LOOP_TIME
            if agent.getIntervalMs() is not None:
                sleepTime = agent.getIntervalMs()/1000 # seconds
            else:
                Sentinel.debug("Using default sleeptime")
            
            startTime = time.monotonic()
            while time.monotonic() - startTime < sleepTime:
                if self.__stop:
                    break
                time.sleep(0.001)  # Check every 1 ms

        # if thread was shutdown abruptly (self.__stop flag), perform shutdown

        if self.__stop:
            Sentinel.debug("Stopping agent")
            agent.shutdownNow()
        
        # cleanup 
        agent.onClose() 
        
        if not self.__stop and self.__runOnFinish is not None:
            # potentially run a task on agent finish
            self.__runOnFinish()
            # clear
            self.__runOnFinish = None
        
        
        # end agent thread
        self.__agentThread = None
        # reset stop flag (even if not stopped)
        self.__stop = False
        # let the world know the agent has finished
        self.__agentFinishEvent.set()
         

    
    def setOnAgentFinished(self,runOnFinish):
        if not self.isShutdown():
            if self.__agentThread is not None:
                self.__runOnFinish = runOnFinish
            else:
                Sentinel.warning("Neo is not alive yet!")
        else:
            Sentinel.warning("Neo has already been shut down!")
    
    def shutDownOnAgentFinished(self):
        self.setOnAgentFinished(self.shutDown)

    def waitForAgentFinished(self):
        if not self.isShutdown():
          if self.__agentThread is not None and self.__agentThread.is_alive():
              Sentinel.info("Waiting for agent to finish...")
              self.__agentFinishEvent.wait()  # Wait until the event is set
              Sentinel.info("Agent has finished.")
              # reset event
              self.__agentFinishEvent.clear()
          else:
              Sentinel.info("No agent to to wait for!")
        else:
            Sentinel.warning("Neo has already been shut down!")
      
    
    def shutDown(self):
        if not self.__isShutdown:
          if self.__agentThread is not None and self.__agentThread.is_alive():
              self.__stop = True
              self.__agentFinishEvent.wait()  # Wait until the event is set (should be instant)
              # ------------ when isFromArchitect is true, process ends here ---------------
              Sentinel.debug("Shut down agent")
          else:
              Sentinel.debug("No agent to shut down.")

          self.__cleanup()          
          
          Sentinel.info("Neo has been shut down")
          self.__printFinish()

          self.__isShutdown = True
        else:
            Sentinel.debug("Already shut down")

    def __cleanup(self):
        # shutdown objects
        self.__propertyOp.deregister() # xtables operation. needs to go before xclient shutdown
        self.__xclient.shutdown()
        self.__mero.shutdown(wait=True,cancel_futures=True)
    
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
