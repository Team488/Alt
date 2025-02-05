import logging
import os
import cv2
import socket
import time
from abc import ABC, abstractmethod
from abstract.LocalizingAgentBase import LocalizingAgentBase
from enum import Enum
from JXTABLES.XTablesClient import XTablesClient
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.FramePacket import FramePacket
from tools.Constants import InferenceMode, getCameraValues
from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools import calibration, NtUtils, configLoader


class CameraName(Enum):
    REARRIGHT = "photonvisionrearright"
    REARLEFT = "photonvisionrearleft"
    FRONTRIGHT = "photonvisionfrontright"
    FRONTLEFT = "photonvisionfrontleft"

    @staticmethod
    def getCameraName():
        name = socket.gethostname()
        return CameraName(name)


class OrangePiAgent(LocalizingAgentBase):
    def create(self):
        super().create()

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

        self.showFrame = self.propertyOperator.createProperty(
            propertyName="showFrame", propertyDefault=False
        )

        self.cap = cv2.VideoCapture(self.CAMERA_INDEX)

        self.Sentinel.info("Creating Frame Processor...")
        self.frameProcessor = LocalFrameProcessor(
            cameraIntrinsics=self.cameraIntrinsics,
            cameraExtrinsics=self.cameraExtrinsics,
            inferenceMode=InferenceMode.RKNN2024,
        )

    def runPeriodic(self):
        super().runPeriodic()
        ret, frame = self.cap.read()
        defaultBytes = b""
        if ret:
            self.Sentinel.debug(f"sending to key{self.device_name}")
            timeStamp = time.time()
            undistortedFrame = calibration.undistortFrame(frame, self.mapx, self.mapy)
            processedResults = self.frameProcessor.processFrame(
                undistortedFrame,
                robotPosXCm=self.robotLocation[0] * 100,  # m to cm
                robotPosYCm=self.robotLocation[1] * 100,  # m to cm
                robotYawRad=self.robotLocation[2],
                drawBoxes=self.showFrame.get(),
            )  # processing as absolute if a robot pose is found
            detectionPacket = DetectionPacket.createPacket(
                processedResults, self.device_name, timeStamp
            )
            # optionally send frame
            if self.showFrame.get():
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
            self.xclient.putBytes(self.device_name, defaultBytes)
            os._exit(1)

    def onClose(self):
        if self.cap.isOpened():
            self.cap.release()

    def isRunning(self):
        if not self.cap.isOpened():
            self.Sentinel.fatal("Camera cant be opened!")
            return False
        return True

    def forceShutdown(self):
        self.cap.release()
        print("Shutdown!")

    @staticmethod
    def getName():
        return "Orange_Pi_Process"

    @staticmethod
    def getDescription():
        return "Ingest_Camera_Run_Ai_Model_Return_Localized_Detections"

    def getIntervalMs(self):
        return 1
