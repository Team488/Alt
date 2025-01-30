import logging
import cv2
import socket
import time
from abc import ABC, abstractmethod
from abstract.Agent import Agent
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


class OrangePiAgent(Agent):
    def create(self):
        self.CAMERA_INDEX = "/dev/color_camera"
        # camera config
        self.calib = self.configOperator.getContent("camera_calib.json")
        self.device_name = CameraName.getCameraName().name
        self.Sentinel.info(f"Camera Name: {self.device_name}")
        # camera values
        self.cameraIntrinsics, self.cameraExtrinsics, _ = getCameraValues(
            self.device_name
        )

        # frame undistortion maps
        self.mapx, self.mapy = calibration.createMapXYForUndistortion(
            self.cameraIntrinsics.getHres(), self.cameraIntrinsics.getVres(), self.calib
        )

        # properties
        self.propertyOperator = self.propertyOperator.getChild(self.device_name)
        # get new property operator with device name
        self.xtablesPosTable = self.propertyOperator.createProperty(
            propertyName="xtablesPosTable", propertyDefault="robot_pose"
        )
        self.ntPosTable = self.propertyOperator.createProperty(
            propertyName="networkTablesPosTable", propertyDefault="/sss"
        )
        self.useXTables = self.propertyOperator.createProperty(
            propertyName="useXtablesForPosition", propertyDefault=False
        )
        self.showFrame = self.propertyOperator.createProperty(
            propertyName="showFrame", propertyDefault=False
        )
        self.detectionPacketTable = self.propertyOperator.createProperty(
            propertyName="table_for_detections", propertyDefault=False
        )
        self.framePacketTable = self.propertyOperator.createProperty(
            propertyName="table_for_frames", propertyDefault=False
        )

        NetworkTables.initialize(server="10.4.88.2")

        self.cap = cv2.VideoCapture(self.CAMERA_INDEX)

        self.Sentinel.info("Creating Frame Processor...")
        self.frameProcessor = LocalFrameProcessor(
            cameraIntrinsics=self.cameraIntrinsics,
            cameraExtrinsics=self.cameraExtrinsics,
            inferenceMode=InferenceMode.RKNN2024,
        )

    def runPeriodic(self):
        ret, frame = self.cap.read()
        defaultBytes = b""
        if ret:
            self.Sentinel.debug(f"sending to key{self.device_name}")
            timeStamp = time.time()
            undistortedFrame = calibration.undistortFrame(frame, self.mapx, self.mapy)
            loc = (0, 0, 0)  # default position x(m),y(m),rotation(rad)
            if self.useXTables.get():
                posebytes = self.xclient.getBytes(self.xtablesPosTable.get())
            else:
                posebytes = NetworkTables.getEntry(self.ntPosTable.get()).get()
            if posebytes:
                loc = NtUtils.getPose2dFromBytes(posebytes)
            else:
                self.Sentinel.warning("Could not get robot pose!!")
            processedResults = self.frameProcessor.processFrame(
                undistortedFrame,
                robotPosXCm=loc[0] * 100,  # m to cm
                robotPosYCm=loc[1] * 100,  # m to cm
                robotYawRad=loc[2],
                drawBoxes=self.showFrame.get(),
            )  # processing as absolute if a robot pose is found
            detectionPacket = DetectionPacket.createPacket(
                processedResults, self.device_name, timeStamp
            )
            # optionally send frame
            if self.showFrame.get:
                framePacket = FramePacket.createPacket(
                    timeStamp, self.device_name, undistortedFrame
                )
                self.xclient.putBytes(
                    f"{self.device_name}_Frame", framePacket.to_bytes()
                )

            # sending network packets
            self.xclient.putBytes(self.device_name, detectionPacket.to_bytes())
        else:
            self.Sentinel.error("Opencv Cap ret is false!")
            self.Sentinel.info("Trying to reopen camera")
            if self.cap.isOpened():
                self.cap.release()
            self.cap = cv2.VideoCapture(self.CAMERA_INDEX)
            self.xclient.putBytes(self.device_name, defaultBytes)

    def onClose(self):
        if self.cap.isOpened():
            self.cap.release()

    def isRunning(self):
        return self.cap.isOpened()

    def shutdownNow(self):
        self.cap.release()
        print("Shutdown!")

    def getName(self):
        return "Orange_Pi_Process"

    def getDescription(self):
        return "Ingest_Camera_Run_Ai_Model_Return_Localized_Detections"

    def getIntervalMs(self):
        return 1
