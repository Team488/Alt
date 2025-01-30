import threading
import time
from logging import Logger
from JXTABLES.XTablesClient import XTablesClient
from abstract.Agent import Agent

# subscribes to command request with xtables and then executes when requested
class AgentOperator:
    DEFAULT_LOOP_TIME = 0.001 # 1 ms
    def __init__(self,xclient : XTablesClient, logger : Logger):
        self.Sentinel = logger
        self.__xclient : XTablesClient = xclient
        self.__agentThread = None # thread to run it
        self.__stop = False # flag
        self.__runOnFinish = None # runnable
        self.__setStatus = lambda agentName, status : self.__xclient.putString(f"agents.{agentName}.Status",status)
        self.__setDescription = lambda agentName, description : self.__xclient.putString(f"agents.{agentName}.Description",description)

    def stop(self):
        self.__stop = True

    def join(self):
        if self.__agentThread is not None:
            self.__agentThread.join()
        else:
            self.Sentinel.warning("No agent thread to join!")
    
    def wakeAgent(self, agent : Agent):
        self.__stop = False # reset stop flag (even if false)
        
        if self.__agentThread is None:
            self.Sentinel.info(f"Waking agent! | Name: {agent.getName()} Description : {agent.getDescription()}")        
            self.__setDescription(agent.getName(),agent.getDescription())  
            self.__setStatus(agent.getName(),"starting")
            self.__agentThread = threading.Thread(target=self.__startAgentLoop,args=[agent])
            self.__agentThread.start()
            # grace period for thread to start
            while not self.__agentThread.is_alive():
                time.sleep(0.001)
            self.Sentinel.info("The agent is alive!")
        else:
            # agenthread already started 
            self.Sentinel.warning("An agent has already been started!")
        
    
    def __startAgentLoop(self, agent : Agent):
        try:
            # create
            progressStr = "create"
            self.__setStatus(agent.getName(),"creating")  
            agent.create()
            
            progressStr = "runPeriodic"
            self.__setStatus(agent.getName(),"running")  
            while agent.isRunning():              
                if self.__stop:
                    break
                agent.runPeriodic()

                sleepTime = self.DEFAULT_LOOP_TIME
                if agent.getIntervalMs() is not None:
                    sleepTime = agent.getIntervalMs()/1000 # seconds
                else:
                    self.Sentinel.debug("Using default sleeptime")
                
                startTime = time.monotonic()
                while time.monotonic() - startTime < sleepTime:
                    time.sleep(0.001)  # Check every 1 ms

            # if thread was shutdown abruptly (self.__stop flag), perform shutdown
            # shutdown before onclose
            forceStopped = self.__stop
            if forceStopped:
                progressStr = "shutDown"
                self.__setStatus(agent.getName(),"shutdown")  
                self.Sentinel.debug("Stopping agent")
                agent.shutdownNow()
            
            # cleanup 
            progressStr = "close"
            self.__setStatus(agent.getName(),f"closing")  
            agent.onClose() 

            if not forceStopped:
                self.__setStatus(agent.getName(),f"agent finished normally")  
                self.Sentinel.debug("Agent has finished normally")

        
        except Exception as e:
            message = f"Failed!\nDuring {progressStr}: {e}"
            self.__setStatus(agent.getName(),message)  
            self.Sentinel.error(message)

        # end agent thread
        self.__agentThread = None

        # potentially run a task on agent finish
        if self.__runOnFinish is not None:
            self.__runOnFinish()
            # clear
            self.__runOnFinish = None
    

    def setOnAgentFinished(self,runOnFinish):
        if self.__agentThread is not None:
                self.__runOnFinish = runOnFinish
        else:
            self.Sentinel.warning("Neo is not alive yet!")

    def waitForAgentFinished(self):
        """ Thread blocking method that waits for a running agent (if any is running)"""
        if self.__agentThread is not None and self.__agentThread.is_alive():
            self.Sentinel.info("Waiting for agent to finish...")
            while self.__agentThread.is_alive():
                time.sleep(0.001)
            self.Sentinel.info("Agent has finished.")
        else:
            self.Sentinel.info("No agent to to wait for!")
        





