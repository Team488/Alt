from typing import Optional, Any
import time

from Alt.Core.Agents import Agent, BindableAgent
from Alt.Core.Constants.Field import Field

from ..Detections.DetectionPacket import DetectionPacket
from ..Inference.ModelConfig import ModelConfig
from ..Localization.PipelineStep2 import PipelineStep2
from .ObjectLocalizingStep1AgentBase import ObjectLocalizingStep1AgentBase


class ObjectLocalizingStep2AgentBase(Agent, BindableAgent):
    """Agent -> (CameraUsingAgentBase, PositionLocalizingAgentBase) -> ObjectLocalizingAgentBase

        Adds inference and object localization capabilites to an agent, processing frames and sending detections
    """

    DETECTIONPOSTFIX = "Detections"

    # TODO this subscriber into a map then check if its updated and then grab latest from the map stuff (below), needs to be consolidated into a single class

    @classmethod
    def bind(cls, 
        modelConfig: ModelConfig,
        field: Field,
    ):
        return super().bind(modelConfig=modelConfig, field=field)

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.field : Field = kwargs.get("field")
        self.modelConfig: ModelConfig = kwargs.get("modelConfig")
        self.finalPipeline: Optional[PipelineStep2] = None

        self.objectupdateMap = {}
        self.localObjectUpdateMap = {}
        self.lastUpdateTimeMs = -1

        self.iterationsPerUpdate = 50
        self.iter_count = 0

    def create(self) -> None:
        super().create()

        self.finalPipeline = PipelineStep2(
            self.modelConfig,
            self.field
        )

    def __addKeyObject(self, key):
        self.objectupdateMap[key] = ([], 0)
        self.localObjectUpdateMap[key] = 0

    # handles a subscriber update from one of the cameras
    def __handleObjectUpdate(self, ret) -> None:
        val = ret.value
        key = ret.key

        lastidx = self.objectupdateMap[key][2]
        lastidx += 1
        if not val or val == b"":
            return
        
        det_packet = DetectionPacket.fromBytes(val)
        # print(f"{det_packet.timestamp=}")
        packet = (DetectionPacket.toResults(det_packet), lastidx)
        self.objectupdateMap[key] = packet

    def __centralUpdate(self) -> None:
        currentTime = time.time() * 1000
        if self.lastUpdateTimeMs == -1:
            timePerLoopMS = 50  # random default value
        else:
            timePerLoopMS = currentTime - self.lastUpdateTimeMs
        self.lastUpdateTimeMs = currentTime

        accumulatedObjectResults = []
        for key in self.localObjectUpdateMap.keys():
            # objects
            localidx = self.localObjectUpdateMap[key]
            resultpacket = self.objectupdateMap[key]
            res, packetidx = resultpacket[:1], resultpacket[1]
            if packetidx != localidx:
                # only update if change
                self.localObjectUpdateMap[key] = packetidx
                accumulatedObjectResults.append(res)

        # update objects
        self.finalPipeline.runStep2(
            cameraResults=accumulatedObjectResults, timeStepMs=timePerLoopMS
        )

    def __periodicSubscribe(self):
        self.updateOp.subscribeAllGlobalUpdates(
            ObjectLocalizingStep1AgentBase.DETECTIONPOSTFIX,
            self.__handleObjectUpdate,
            runOnNewSubscribe=self.__addKeyObject,
        )

    def runPeriodic(self) -> None:
        super().runPeriodic()
        self.__centralUpdate()
        self.iter_count += 1
        if self.iter_count == self.iterationsPerUpdate:
            # reset the count
            self.iter_count = 0
            self.__periodicSubscribe()

    def onClose(self) -> None:
        super().onClose()
        self.updateOp.unsubscribeToAllGlobalUpdates(
            ObjectLocalizingStep1AgentBase.DETECTIONPOSTFIX, self.__handleObjectUpdate
        )

    def getDescription(self):
        return "Central-Process-Accumulate-Results-Broadcast-Them"

    def isRunning(self):
        return True


