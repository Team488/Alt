from functools import partial
import math
import time

import cv2
import numpy as np

from Core.Agents.Abstract.CameraUsingAgentBase import CameraUsingAgentBase
from reefTracking.reefTracker import ReefTracker
from tools.Constants import CameraExtrinsics, CameraIntrinsics
from coreinterface.ReefPacket import ReefPacket


class ReefTrackingAgentBase(CameraUsingAgentBase):
    OBSERVATIONPOSTFIX = "OBSERVATIONS"
    """ Agent -> (CameraUsingAgentBase, PositionLocalizingAgentBase) -> TimestampRegulatedAgentBase -> ReefTrackingAgentBase
        This agent adds reef tracking capabilites. Must be used as partial
        If showFrames is True, you must run this agent as main
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.cameraIntrinsics = kwargs.get("cameraIntrinsics", None)

    def create(self) -> None:
        super().create()
        self.tracker = ReefTracker(
            cameraIntrinsics=self.cameraIntrinsics, isLocalAT=True
        )
        self.reefProp = self.propertyOperator.createCustomReadOnlyProperty(
            self.OBSERVATIONPOSTFIX, b""
        )
        if not self.oakMode:
            CameraIntrinsics.setCapRes(self.cameraIntrinsics, self.cap)
        self.c = 0

    def runPeriodic(self) -> None:
        super().runPeriodic()
        outCoral, outAlgae = self.tracker.getAllTracks(
            self.latestFrame, drawBoxes=self.showFrames
        )
        reefPkt = ReefPacket.createPacket(
            outCoral, outAlgae, "helloo", time.time() * 1000
        )
        self.reefProp.set(reefPkt.to_bytes())

        # if self.c < 50:
        #     cv2.imwrite(f"assets/Frame#{self.c}.jpg",self.latestFrame)
        #     self.c+=1
        # time.sleep(1)

    def getName(self) -> str:
        return "Reef_Tracking_Agent"

    def getDescription(self) -> str:
        return "Gets_Reef_State"


def ReefTrackingAgentPartial(cameraPath, cameraIntrinsics, showFrames=False):
    """Returns a partially completed ReefTrackingAgent agent. All you have to do is pass it into neo"""
    return partial(
        ReefTrackingAgentBase,
        cameraPath=cameraPath,
        cameraIntrinsics=cameraIntrinsics,
        showFrames=showFrames,
    )
