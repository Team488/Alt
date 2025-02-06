import time

import cv2
from tools.Constants import CameraIdOffsets
from coreinterface.FramePacket import FramePacket
from abstract.Agent import Agent
from abstract.FrameProcessingAgentBase import FrameProcessingAgent


class FrameDisplayer(Agent):
    """Agent -> FrameDisplayer

    Agent that will automatically ingest frames and display them\n
    NOTE: Due to openCVs nature this agent must be run in the main thread\n
    SEE: Neo.wakeAgentMain()
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
        self.getFrameTable = (
            lambda key: f"{self.keyToHost.get(key)}.{FrameProcessingAgent.FRAMEPOSTFIX}"
        )

        self.updateMap = {key: None for key in self.keys}
        self.lastUpdateTimeMs = -1
        for key in self.keys:
            # subscribe to detection packets
            self.xclient.subscribe(
                self.getFrameTable(key),
                consumer=lambda ret: self.__handleUpdate(key, ret),
            )

        self.runFlag = True  # will be used with cv2 waitkey

    # handles a subscriber update from one of the cameras
    def __handleUpdate(self, key, ret):
        val = ret.value

        if not val or val == b"":
            return

        frame_pkt = FramePacket.fromBytes(val)
        frame = FramePacket.getFrame(frame_pkt)
        self.updateMap[key] = frame

    def __showFrames(self):
        for key in self.updateMap.keys():
            frame = self.updateMap.get(key)
            if frame is not None:
                cv2.imshow(key, frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.runFlag = False

    def runPeriodic(self):
        super().runPeriodic()
        self.__showFrames()

    def onClose(self):
        super().onClose()
        cv2.destroyAllWindows()
        for key in self.keys:
            self.xclient.unsubscribe(
                self.getFrameTable(key), consumer=self.__handleUpdate
            )

    def isRunning(self):
        return self.runFlag

    @staticmethod
    def getName():
        return "Frame_Displaying_Agent"

    @staticmethod
    def getDescription():
        return "Ingest_Frames_Show_Them"
