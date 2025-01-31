import logging
import cv2
import socket
import time
from abc import ABC, abstractmethod
from abstract.CentralAgentBase import CentralAgent
from enum import Enum
from JXTABLES.XTablesClient import XTablesClient
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.FramePacket import FramePacket
from tools.Constants import InferenceMode, getCameraValues
from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools import calibration, NtUtils, configLoader
from networktables import NetworkTables


class CameraName(Enum):
    REARRIGHT = "photonvisionrearright"
    REARLEFT = "photonvisionrearleft"
    FRONTRIGHT = "photonvisionfrontright"
    FRONTLEFT = "photonvisionfrontleft"

    def getCameraName():
        name = socket.gethostname()
        return CameraName(name)


class OrangePiAgent(CentralAgent):
    def create(self):
        super().create()
        pathTable = self.propertyOperator.createProperty("Path_Location", "target_waypoints")
        targetX = self.propertyOperator.createProperty("targetX",100)
        targetY = self.propertyOperator.createProperty("targetY",100)
        hasGeneratedPath = self.propertyOperator.createReadOnlyProperty("hasGenerated",False)
        

    def runPeriodic(self):
        super().runPeriodic()
        # self.central.pathGenerator.generate()

    def onClose(self):
        super().onClose()


    def isRunning(self):
        return True

    def forceShutdown(self):
        print("Shutdown!")

    def getName(self):
        return "PathPlanning_Agent"

    def getDescription(self):
        return "Ingest_Detections_Give_Path"

    def getIntervalMs(self):
        return 1
