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
from tools.Constants import InferenceMode, CameraExtrinsics, CameraIntrinsics
from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools import calibration, NtUtils, configLoader


class InferenceAgent(Agent):
    def create(self):
        self.device_name = "test"
        self.CAMERA_INDEX = "assets/video12qual25clipped.mp4"
        # camera config

        self.cap = cv2.VideoCapture(self.CAMERA_INDEX)

        self.Sentinel.info("Creating Frame Processor...")
        self.frameProcessor = LocalFrameProcessor(
            cameraIntrinsics=CameraIntrinsics.OV9782COLOR,
            cameraExtrinsics=CameraExtrinsics.NONE,
            inferenceMode=InferenceMode.ONNX2024,
        )
        self.frameProp = self.propertyOperator.createReadOnlyProperty(f"{self.device_name}_Frame", "")

    def runPeriodic(self):
        ret, frame = self.cap.read()
        defaultBytes = b""
        if ret:    
            timestamp = time.monotonic()        
            processedResults = self.frameProcessor.processFrame(
                frame,
                drawBoxes=True,
            )  
            framePacket = FramePacket.createPacket(
                timestamp, self.device_name, frame
            )
            self.frameProp.set(framePacket.to_bytes())
            self.Sentinel.info("Processed frame!")

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
        if not self.cap.isOpened():
            self.Sentinel.fatal("Camera cant be opened!")
            return False
        return True

    def forceShutdown(self):
        self.cap.release()
        print("Shutdown!")

    @staticmethod
    def getName():
        return "Inference_Agent_Process"

    @staticmethod
    def getDescription():
        return "Ingest_Camera_Run_Ai_Model"

    def getIntervalMs(self):
        return 1
