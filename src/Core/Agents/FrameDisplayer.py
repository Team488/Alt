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
        self.getSendEnableTable = (
            lambda key: f"{key}.{CameraUsingAgentBase.FRAMETOGGLEPOSTFIX}"
        )
        self.updateMap = {}
        self.keys = set()

        self.runFlag = True  # will be used with cv2 waitkey
        self.displayedFrames = self.propertyOperator.createReadOnlyProperty(
            "Showed_Frames", False
        )

    def subscribeFrameUpdate(self):
        self.updateOp.subscribeAllGlobalUpdates(
            CameraUsingAgentBase.FRAMEPOSTFIX,
            updateSubscriber=self.__handleUpdate,
            runOnNewSubscribe=self.addKey,
            runOnRemoveSubscribe=self.removeKey,
        )

    def __handleUpdate(self, ret) -> None:
        val = ret.value

        if not val or val == b"":
            return

        frame_pkt = FramePacket.fromBytes(val)
        frame = FramePacket.getFrame(frame_pkt)
        self.updateMap[ret.key] = frame

    def __showFrames(self) -> None:
        showedFrames = False
        if len(self.updateMap.keys()) > 0:
            copy = dict(self.updateMap.items()) # copy
            for key, item in copy.items():
                frame = item
                if frame is not None:
                    cv2.imshow(key, frame)
                    showedFrames = True

        self.displayedFrames.set(showedFrames)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.runFlag = False

    def addKey(self, key: str):
        cut = key[: key.rfind(".")]
        full = f"{cut}.{CameraUsingAgentBase.FRAMETOGGLEPOSTFIX}"
        self.xclient.putBoolean(full, True)
        print(f"{key=} added")
        print(f"{full=} set to True")
        # cv2.namedWindow(key)

    def removeKey(self, key):
        cut = key[: key.rfind(".")]
        full = f"{cut}.{CameraUsingAgentBase.FRAMETOGGLEPOSTFIX}"
        self.xclient.putBoolean(full, False)
        print(f"{key=} removed")
        print(f"{full=} set to False")
        try:
            cv2.destroyWindow(key)
            cv2.waitKey(1)
        except Exception as e:
            print(e)
            pass

    def runPeriodic(self) -> None:
        super().runPeriodic()
        self.subscribeFrameUpdate()
        self.__showFrames()

    def onClose(self) -> None:
        super().onClose()
        self.updateOp.unsubscribeToAllGlobalUpdates(
            CameraUsingAgentBase.FRAMEPOSTFIX, self.__handleUpdate
        )
        cv2.destroyAllWindows()

    def isRunning(self):
        return self.runFlag

    def getName(self) -> str:
        return "Frame_Displaying_Agent"

    def getDescription(self) -> str:
        return "Ingest_Frames_Show_Them"
