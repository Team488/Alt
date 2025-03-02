import time

import cv2
from Core.Agents.Abstract.CameraUsingAgentBase import CameraUsingAgentBase
from tools.Constants import CameraIdOffsets2024
from coreinterface.FramePacket import FramePacket
from abstract.Agent import Agent


class FrameDisplayer(Agent):
    """Agent -> FrameDisplayer

    Agent that will automatically ingest frames and display them\n
    NOTE: Due to openCVs nature this agent must be run in the main thread\n
    """

    def create(self) -> None:
        super().create()
        # perform agent init here (eg open camera or whatnot)
        self.keys = set()

        self.getFrameTable = lambda key: f"{key}.{CameraUsingAgentBase.FRAMEPOSTFIX}"
        self.getSendEnableTable = (
            lambda key: f"{key}.{CameraUsingAgentBase.FRAMETOGGLEPOSTFIX}"
        )

        self.runFlag = True  # will be used with cv2 waitkey
        self.displayedFrames = self.propertyOperator.createReadOnlyProperty(
            "Showed_Frames", False
        )

    def addKey(self, key):
        self.xclient.putBoolean(self.getSendEnableTable(key), True)
        cv2.namedWindow(key)

    def removeKey(self, key):
        self.xclient.putBoolean(self.getSendEnableTable(key), False)
        try:
            cv2.destroyWindow(key)
        except Exception:
            pass

    def updateInternal(self, currentHostnames):
        # old keys removed
        remove = []
        for pastKey in self.keys:
            if pastKey not in currentHostnames:
                self.removeKey(pastKey)
                remove.add(pastKey)

        for remKey in remove:
            self.keys.remove(remKey)

        # new keys added
        for newKey in currentHostnames:
            if newKey not in self.keys:
                self.addKey(newKey)
                self.keys.add(newKey)

    def getAllRunningHostNames(self) -> list[str]:
        return self.xclient.getStringList(CameraUsingAgentBase.RUNNINGHOSTNAMES)

    def runPeriodic(self) -> None:
        super().runPeriodic()
        hostNames = self.getAllRunningHostNames()
        self.updateInternal(hostNames)

        for key in self.keys:
            table = self.getFrameTable(key)
            frame_bytes = self.xclient.getUnknownBytes(table)
            if frame_bytes is not None and frame_bytes is not b"":
                framePkt = FramePacket.fromBytes(frame_bytes)
                frame = FramePacket.getFrame(framePkt)
                cv2.imshow(key, frame)
                self.displayedFrames.set(True)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.runFlag = False

    def onClose(self) -> None:
        super().onClose()
        cv2.destroyAllWindows()
        for key in self.keys:
            self.removeKey(key)

    def isRunning(self):
        return self.runFlag

    def getName(self) -> str:
        return "Frame_Displaying_Agent"

    def getDescription(self) -> str:
        return "Ingest_Frames_Show_Them"
