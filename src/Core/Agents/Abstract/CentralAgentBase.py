import time
from tools.Constants import CameraIdOffsets, ATLocations, Units, TEAM
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.ReefPacket import ReefPacket
from abstract.Agent import Agent
from Core.Agents.Abstract.ObjectLocalizingAgentBase import ObjectLocalizingAgentBase
from Core.Agents.Abstract.ReefTrackingAgentBase import ReefTrackingAgentBase
from Core.Agents.Abstract.PositionLocalizingAgentBase import PositionLocalizingAgentBase


class CentralAgentBase(PositionLocalizingAgentBase):
    """Agent -> CentralAgentBase

    Adds automatic ingestion of detection packets into the central process
    """

    def create(self):
        super().create()
        # perform agent init here (eg open camera or whatnot)
        self.keys = ["REARRIGHT", "REARLEFT", "FRONTLEFT", "FRONTRIGHT", "Johnny"]
        self.keyToHost = {
            "REARRIGHT": "photonvisionrearright",
            "REARLEFT": "photonvisionrearleft",
            "FRONTLEFT": "photonvisionfrontleft",
            "FRONTRIGHT": "photonvisionfrontright",
            "FRONTRIGHT": "Adem-Laptop",
            "Johnny": "archlinux",
        }
        print("CREATED HOST")
        self.getDetectionTable = (
            lambda key: f"{self.keyToHost.get(key)}.{ObjectLocalizingAgentBase.DETECTIONPOSTFIX}"
        )
        self.getReefTable = (
            lambda key: f"{self.keyToHost.get(key)}.{ReefTrackingAgentBase.OBSERVATIONPOSTFIX}"
        )
        self.objectupdateMap = {key: ([], 0, 0) for key in self.keys}
        self.localObjectUpdateMap = {key: 0 for key in self.keys}
        self.reefupdateMap = {key: ([], 0) for key in self.keys}
        self.localReefUpdateMap = {key: 0 for key in self.keys}
        self.lastUpdateTimeMs = -1
        for key in self.keys:
            # subscribe to detection packets
            self.xclient.subscribe(
                self.getDetectionTable(key),
                consumer=lambda ret: self.__handleObjectUpdate(key, ret),
            )
            # subscribe to reef packets
            self.xclient.subscribe(
                self.getReefTable(key),
                consumer=lambda ret: self.__handleReefUpdate(key, ret),
            )

        self.clAT = self.propertyOperator.createCustomReadOnlyProperty(
            "BESTOPENREEF_AT", None, addBasePrefix=False
        )
        self.clBR = self.propertyOperator.createCustomReadOnlyProperty(
            "BESTOPENREEFBRANCH", None, addBasePrefix=False
        )
        self.brx = self.propertyOperator.createCustomReadOnlyProperty(
            "BESTROBOTX", None, addBasePrefix=False
        )
        self.bry = self.propertyOperator.createCustomReadOnlyProperty(
            "BESTROBOTY", None, addBasePrefix=False
        )

        self.reefmap_states = self.propertyOperator.createCustomReadOnlyProperty(
            "REEFMAP_STATES", None, addBasePrefix=False
        )

    # handles a subscriber update from one of the cameras
    def __handleObjectUpdate(self, key, ret):
        val = ret.value
        idOffset = CameraIdOffsets[key]
        lastidx = self.objectupdateMap[key][2]
        lastidx += 1
        if not val or val == b"":
            return
        det_packet = DetectionPacket.fromBytes(val)
        # print(f"{det_packet.timestamp=}")
        packet = (DetectionPacket.toDetections(det_packet), idOffset, lastidx)
        self.objectupdateMap[key] = packet

    def __handleReefUpdate(self, key, ret):
        val = ret.value
        lastidx = self.reefupdateMap[key][1]
        lastidx += 1
        if not val or val == b"":
            return
        reef_packet = ReefPacket.fromBytes(val)
        # print(f"{det_packet.timestamp=}")
        packet = (ReefPacket.getFlattenedObservations(reef_packet), lastidx)
        self.reefupdateMap[key] = packet

    def __centralUpdate(self):
        currentTime = time.time() * 1000
        if self.lastUpdateTimeMs == -1:
            timePerLoopMS = 50  # random default value
        else:
            timePerLoopMS = currentTime - self.lastUpdateTimeMs
        self.lastUpdateTimeMs = currentTime

        accumulatedObjectResults = []
        accumulatedReefResults = []
        for key in self.keys:
            # objects
            localidx = self.localObjectUpdateMap[key]
            resultpacket = self.objectupdateMap[key]
            res, packetidx = resultpacket[:2], resultpacket[2]
            if packetidx != localidx:
                # no update same id
                self.localObjectUpdateMap[key] = packetidx
                accumulatedObjectResults.append(res)

            # reef
            localidx = self.localReefUpdateMap[key]
            resultpacket = self.reefupdateMap[key]
            res, packetidx = resultpacket[0], resultpacket[1]
            if packetidx != localidx:
                # no update same id
                self.localReefUpdateMap[key] = packetidx
                accumulatedReefResults.append(res)

        # update objects
        self.central.processFrameUpdate(
            cameraResults=accumulatedObjectResults, timeStepMs=timePerLoopMS
        )
        # update reef
        self.central.processReefUpdate(
            reefResults=accumulatedReefResults, timeStepMs=timePerLoopMS
        )

    def runPeriodic(self):
        super().runPeriodic()
        self.__centralUpdate()
        self.putBestNetworkValues()

    def putBestNetworkValues(self):
        # Send the ReefPacket for the entire map
        import time
        timestamp = time.time()
        mapstate_packet = self.central.reefState.getReefMapState_as_ReefPacket(team=TEAM.BLUE, timestamp=timestamp)
        bytes = mapstate_packet.to_bytes()
        self.reefmap_states.set(bytes)
        
        # Send the confidence of highest algae
        highest_algae = self.central.objectmap.getHighestRobot()
        self.brx.set(highest_algae[0])
        self.bry.set(highest_algae[1])

        closest_At, closest_branch = self.central.reefState.getClosestOpen(
            self.robotPose2dCMRAD, threshold=0.0
        )
        print("closeAT and closeBranch", closest_At, closest_branch)
        self.clAT.set(closest_At)
        self.clBR.set(closest_branch)

    def onClose(self):
        super().onClose()
        for key in self.keys:
            self.xclient.unsubscribe(
                self.getDetectionTable(key), consumer=self.__handleObjectUpdate
            )
