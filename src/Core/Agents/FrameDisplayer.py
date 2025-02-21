import time

import cv2
from tools.Constants import CameraIdOffsets
from coreinterface.FramePacket import FramePacket
from abstract.Agent import Agent
from Core.Agents.Abstract.ObjectLocalizingAgentBase import ObjectLocalizingAgentBase


class FrameDisplayer(Agent):
    """Agent -> FrameDisplayer

    Agent that will automatically ingest frames and display them\n
    NOTE: Due to openCVs nature this agent must be run in the main thread\n
    """

    def create(self):
        super().create()
        # perform agent init here (eg open camera or whatnot)
        self.keyToHost = {
            "REARRIGHT": "photonvisionrearright",
            "FRONTRIGHT": "photonvisionfrontright",
            "REARLEFT": "photonvisionrearleft",
            "FRONTLEFT": "photonvisionfrontleft",
            # "ademlaptop": "Adem-Laptop",
            # "ademGamingPC": "Adem-GamingPc",
        }
        self.getFrameTable = (
            lambda key: f"{self.keyToHost.get(key)}.{ObjectLocalizingAgentBase.FRAMEPOSTFIX}"
        )

        self.updateMap = {key: None for key in self.keyToHost.keys()}
        self.lastUpdateTimeMs = -1
        for key in self.keyToHost.keys():
            # subscribe to detection packets
            self.xclient.subscribe(
                self.getFrameTable(key),
                consumer=lambda ret: self.__handleUpdate(key, ret),
            )

        self.runFlag = True  # will be used with cv2 waitkey
        self.displayedFrames = self.propertyOperator.createReadOnlyProperty(
            "Showed_Frames", False
        )

    # handles a subscriber update from one of the cameras
    def __handleUpdate(self, key, ret):
        val = ret.value

        if not val or val == b"":
            return

        frame_pkt = FramePacket.fromBytes(val)
        frame = FramePacket.getFrame(frame_pkt)
        self.updateMap[key] = frame

    def __showFrames(self):
        showedFrames = False
        for key in self.updateMap.keys():
            frame = self.updateMap.get(key)
            if frame is not None:
                cv2.imshow(key, frame)
                showedFrames = True

        self.displayedFrames.set(showedFrames)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.runFlag = False

    def runPeriodic(self):
        super().runPeriodic()
        self.__showFrames()

    def onClose(self):
        super().onClose()
        cv2.destroyAllWindows()
        for key in self.keyToHost.keys():
            self.xclient.unsubscribe(
                self.getFrameTable(key), consumer=self.__handleUpdate
            )

    def isRunning(self):
        return self.runFlag

    def getName(self):
        return "Frame_Displaying_Agent"

    def getDescription(self):
        return "Ingest_Frames_Show_Them"
