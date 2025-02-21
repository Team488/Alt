import time
from tools.Constants import CameraIdOffsets
from coreinterface.DetectionPacket import DetectionPacket
from abstract.Agent import Agent
from Core.Agents.Abstract.ObjectLocalizingAgentBase import ObjectLocalizingAgentBase


class CentralAgentBase(Agent):
    """Agent -> CentralAgentBase

    Adds automatic ingestion of detection packets into the central process
    """

    def create(self):
        super().create()
        # perform agent init here (eg open camera or whatnot)
        self.keys = ["REARRIGHT", "REARLEFT", "FRONTLEFT", "FRONTRIGHT"]
        self.keyToHost = {
            "REARRIGHT": "photonvisionrearright",
            "REARLEFT": "photonvisionrearleft",
            "FRONTLEFT": "photonvisionfrontleft",
            "FRONTRIGHT": "photonvisionfrontright",
        }
        self.getDetectionTable = (
            lambda key: f"{self.keyToHost.get(key)}.{ObjectLocalizingAgentBase.DETECTIONPOSTFIX}"
        )
        self.updateMap = {key: ([], 0, 0) for key in self.keys}
        self.localUpdateMap = {key: 0 for key in self.keys}
        self.lastUpdateTimeMs = -1
        for key in self.keys:
            # subscribe to detection packets
            self.xclient.subscribe(
                self.getDetectionTable(key),
                consumer=lambda ret: self.__handleUpdate(key, ret),
            )

    # handles a subscriber update from one of the cameras
    def __handleUpdate(self, key, ret):
        val = ret.value
        idOffset = CameraIdOffsets[key]
        lastidx = self.updateMap[key][2]
        lastidx += 1
        if not val or val == b"":
            return
        det_packet = DetectionPacket.fromBytes(val)
        # print(f"{det_packet.timestamp=}")
        packet = (DetectionPacket.toDetections(det_packet), idOffset, lastidx)
        self.updateMap[key] = packet

    def __centralUpdate(self):
        currentTime = time.time() * 1000
        if self.lastUpdateTimeMs == -1:
            timePerLoop = 50  # random default value
        else:
            timePerLoop = currentTime - self.lastUpdateTimeMs
        self.lastUpdateTimeMs = currentTime
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
            cameraResults=accumulatedResults, timeStepSeconds=timePerLoop
        )

    def runPeriodic(self):
        super().runPeriodic()
        self.__centralUpdate()

    def onClose(self):
        super().onClose()
        for key in self.keys:
            self.xclient.unsubscribe(
                self.getDetectionTable(key), consumer=self.__handleUpdate
            )
