import time
from tools.Constants import CameraIdOffsets
from coreinterface.DetectionPacket import DetectionPacket
from abstract.Agent import Agent


class CentralAgentBase(Agent):
    """ Agent -> CentralAgentBase

        Adds automatic ingestion of detection packets into the central process
    """
    def create(self):        
        super().create()
        # perform agent init here (eg open camera or whatnot)
        self.keys=["REARRIGHT", "REARLEFT", "FRONTLEFT", "FRONTRIGHT"]
        self.updateMap = {key: ([], 0, 0) for key in self.keys}
        self.localUpdateMap = {key: 0 for key in self.keys}
        self.lastUpdateTimeMs = -1
        for key in self.keys:
            self.xclient.subscribe(key, consumer=self.__handleUpdate)

    # handles a subscriber update from one of the cameras
    def __handleUpdate(self, ret):
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
            self.xclient.unsubscribe(key, consumer=self.__handleUpdate)
