import datetime
from functools import partial
import math
import time

import cv2
import numpy as np

from Core.Agents.Abstract.CameraUsingAgentBase import CameraUsingAgentBase
from abstract.Capture import ConfigurableCapture
from reefTracking import reefTracker
from reefTracking.reefTracker import ReefTracker
from reefTracking.poseSolver import poseSolver
from tools.Constants import ATLocations, CameraExtrinsics, CameraIntrinsics
from coreinterface.ReefPacket import ReefPacket
from tools.Units import LengthType


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
        self.poseSolver = poseSolver()
        self.tracker = ReefTracker(cameraIntrinsics=self.cameraIntrinsics)

        self.putNetworkInfo()

    def putNetworkInfo(self):
        getReadable = lambda time: datetime.datetime.fromtimestamp(time).strftime(
            "%Y-%m-%d %H:%M:%S"
        )
        purpleHistMtime = reefTracker.purpleHistMTime
        whiteHistMtime = reefTracker.whiteHistMTime
        algaeHistMtime = reefTracker.algaeHistMTime

        self.propertyOperator.createReadOnlyProperty(
            "ReefTracker.PurpleReefPostHist.TimeStamp", getReadable(purpleHistMtime)
        )
        self.propertyOperator.createReadOnlyProperty(
            "ReefTracker.WhiteCoralHist.TimeStamp", getReadable(whiteHistMtime)
        )
        self.propertyOperator.createReadOnlyProperty(
            "ReefTracker.AlgaeHist.TimeStamp", getReadable(algaeHistMtime)
        )

    def runPeriodic(self) -> None:
        super().runPeriodic()
        outCoral, outAlgae, atOutput = self.tracker.getAllTracks(
            self.latestFrameCOLOR, drawBoxes=self.showFrames or self.sendFrame
        )
        self.latestPoseREEF = self.poseSolver.getLatestPoseEstimate(atOutput)
        # print(self.latestPoseREEF)

        reefPkt = ReefPacket.createPacket(
            outCoral, outAlgae, "helloo", time.time() * 1000
        )
        self.updateOp.addGlobalUpdate(self.OBSERVATIONPOSTFIX, reefPkt.to_bytes())

    def getName(self) -> str:
        return "Reef_Tracking_Agent"

    def getDescription(self) -> str:
        return "Gets_Reef_State"


def ReefTrackingAgentPartial(capture: ConfigurableCapture, showFrames=False):
    """Returns a partially completed ReefTrackingAgent agent. All you have to do is pass it into neo"""
    return partial(
        ReefTrackingAgentBase,
        capture=capture,
        cameraIntrinsics=capture.getIntrinsics(),
        showFrames=showFrames,
    )
