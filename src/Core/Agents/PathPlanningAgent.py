import logging
import cv2
import socket
import time
from abc import ABC, abstractmethod
from abstract.CentralAgentBase import CentralAgent
from enum import Enum
from JXTABLES import XTableValues_pb2
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.FramePacket import FramePacket
from tools.Constants import InferenceMode, getCameraValues
from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools import calibration, NtUtils, configLoader, UnitConversion
from networktables import NetworkTables


class DriveToTargetAgent(CentralAgent):
    def create(self):
        super().create()
        self.xtablesPosTable = self.propertyOperator.createProperty(
            propertyName="xtablesPosTable", propertyDefault="robot_pose"
        )
        self.ntPosTable = self.propertyOperator.createProperty(
            propertyName="networkTablesPosTable",
            propertyDefault="AdvantageKit/RealOutputs/PoseSubsystem/RobotPose",
        )
        self.useXTables = self.propertyOperator.createProperty(
            propertyName="useXtablesForPosition", propertyDefault=False
        )
        self.pathTable = self.propertyOperator.createProperty(
            "Path_Location", "target_waypoints"
        )
        self.targetConf = self.propertyOperator.createProperty("targetMinConf", 0.3)
        self.bestConf = self.propertyOperator.createReadOnlyProperty(
            "currentTargetBestConf", 0
        )
        NetworkTables.initialize(server="10.4.88.2")
        posePath: str = self.ntPosTable.get()
        entryIdx = posePath.rfind("/")
        self.poseTable = posePath[:entryIdx]
        self.poseEntry = posePath[entryIdx + 1 :]
        self.table = NetworkTables.getTable(self.poseTable)
        self.ntpos = self.table.getEntry(self.poseEntry)

    def runPeriodic(self):
        super().runPeriodic()

        loc = (0, 0, 0)  # default position x(m),y(m),rotation(rad)
        if self.useXTables.get():
            posebytes = self.xclient.getUnknownBytes(self.xtablesPosTable.get())
        else:
            posebytes = self.ntpos.get()
        if posebytes:
            loc = NtUtils.getPose2dFromBytes(posebytes)
        else:
            self.Sentinel.warning("Could not get robot pose!!")

        target = self.central.map.getHighestGameObject()
        conf = target[2]
        self.bestConf.set(float(conf))
        if conf > self.targetConf.get():
            path = self.central.pathGenerator.generate(
                (loc[0] * 100, loc[1] * 100), target[:2]
            )
            coordinates = []
            for waypoint in path:
                element = XTableValues_pb2.Coordinate(
                    x=waypoint[0] / 100, y=waypoint[1] / 100
                )
                coordinates.append(element)
            self.xclient.putCoordinates(self.pathTable.get(), coordinates)
            self.Sentinel.info("Generated path")
        else:
            self.xclient.putCoordinates(self.pathTable.get(), [])
            self.Sentinel.info("Failed to generate path")

    def onClose(self):
        super().onClose()

    def isRunning(self):
        return True

    def forceShutdown(self):
        print("Shutdown!")

    @staticmethod
    def getName():
        return "PathPlanning_Agent"

    @staticmethod
    def getDescription():
        return "Ingest_Detections_Give_Path"

    def getIntervalMs(self):
        return 1


class DriveToFixedPointAgent(CentralAgent):
    def create(self):
        super().create()
        self.xtablesPosTable = self.propertyOperator.createProperty(
            propertyName="xtablesPosTable", propertyDefault="robot_pose"
        )
        self.ntPosTable = self.propertyOperator.createProperty(
            propertyName="networkTablesPosTable",
            propertyDefault="AdvantageKit/RealOutputs/PoseSubsystem/RobotPose",
        )
        self.useXTables = self.propertyOperator.createProperty(
            propertyName="useXtablesForPosition", propertyDefault=False
        )
        self.targetX = self.propertyOperator.createProperty(
            propertyName="targetX", propertyDefault=2
        )
        self.targetY = self.propertyOperator.createProperty(
            propertyName="targetY", propertyDefault=2
        )
        self.pathTable = self.propertyOperator.createProperty(
            "Path_Location", "target_waypoints"
        )
        NetworkTables.initialize(server="10.4.88.2")
        posePath: str = self.ntPosTable.get()
        entryIdx = posePath.rfind("/")
        self.poseTable = posePath[:entryIdx]
        self.poseEntry = posePath[entryIdx + 1 :]
        self.table = NetworkTables.getTable(self.poseTable)
        self.ntpos = self.table.getEntry(self.poseEntry)

    def runPeriodic(self):
        super().runPeriodic()

        loc = (0, 0, 0)  # default position x(m),y(m),rotation(rad)
        if self.useXTables.get():
            posebytes = self.xclient.getUnknownBytes(self.xtablesPosTable.get())
        else:
            posebytes = self.ntpos.get()
        if posebytes:
            loc = NtUtils.getPose2dFromBytes(posebytes)
        else:
            self.Sentinel.warning("Could not get robot pose!!")

        target = (self.targetX.get() * 100, self.targetY.get() * 100)
        self.Sentinel.info(f"{loc=} {target=}")
        path = self.central.pathGenerator.generate((loc[0] * 100, loc[1] * 100), target)
        if path:
            coordinates = []
            for waypoint in path:
                element = XTableValues_pb2.Coordinate(
                    x=waypoint[0] / 100, y=waypoint[1] / 100
                )
                coordinates.append(element)
            self.xclient.putCoordinates(self.pathTable.get(), coordinates)
            self.Sentinel.info(path)
            self.Sentinel.info("Generated path")
        else:
            self.Sentinel.info("No path!")
            self.xclient.putCoordinates(self.pathTable.get(), [])

        self.Sentinel.info(f"{target=}")

    def onClose(self):
        super().onClose()

    def isRunning(self):
        return True

    def forceShutdown(self):
        print("Shutdown!")

    @staticmethod
    def getName():
        return "PathPlanning_Agent"

    @staticmethod
    def getDescription():
        return "Ingest_Detections_Give_Path"

    def getIntervalMs(self):
        return 1
