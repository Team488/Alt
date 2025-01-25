import cv2
import argparse
import logging
import time
import numpy as np
from tools.Constants import CameraIdOffsets
from JXTABLES.XTablesClient import XTablesClient
from JXTABLES import XTableValues_pb2
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.FramePacket import FramePacket
from mapinternals.CentralProcessor import CentralProcessor
from pathplanning.PathGenerator import PathGenerator
from tools import NtUtils
class MainProcessInterface:
    def __init__(self,xclient,ntclient, keys = ["REARRIGHT", "REARLEFT", "FRONTLEFT", "FRONTRIGHT"]):
        """ Process to run on orin """
        self.central = CentralProcessor.instance()
        self.xclient = xclient
        self.ntclient = ntclient
        self.keys = keys
        self.updateMap = {
            key: ([], 0, 0) for key in self.keys
        }
        self.localUpdateMap =  {key: 0 for key in self.keys}
        self.lastUpdateTimeMs = -1
        self.registerCallBacks()


    def registerCallBacks(self):
        for key in self.keys:
            self.xclient.subscribe(key, consumer=self.__handle_update)

    def __handle_update(self,ret):
        key = ret.key
        val = ret.value
        idOffset = CameraIdOffsets[key]
        lastidx = self.updateMap[key][2]
        lastidx += 1
        if not key or not val:
            return
        if val == b"":
            self.updateMap[key] = ([], idOffset, lastidx)
            return
        det_packet = DetectionPacket.fromBytes(val)
        # print(f"{det_packet.timestamp=}")
        packet = (DetectionPacket.toDetections(det_packet), idOffset, lastidx)
        self.updateMap[key] = packet

    def central_update(self):
        currentTime = time.time()*1000
        if self.lastUpdateTimeMs == -1:
            timePerLoop = 50 # some default value
        else:
            timePerLoop = (currentTime-self.lastUpdateTimeMs)
        self.lastUpdateTimeMs = currentTime
        TIMEPERLOOPMS = 50  # ms
        accumulatedResults = []
        for key in self.keys:
            localidx = self.localUpdateMap[key]
            resultpacket = self.updateMap[key]
            res, packetidx = resultpacket[:2], resultpacket[2]
            if packetidx == localidx:
                # no update same id
                continue
            self.localUpdateMap[key] = packetidx
            accumulatedResults.append(res)
        self.central.processFrameUpdate(
            cameraResults=accumulatedResults, timeStepSeconds=TIMEPERLOOPMS / 1000
        )
