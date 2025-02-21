from functools import partial
import math

import cv2
import numpy as np

from Core.Agents.Abstract.CameraUsingAgentBase import CameraUsingAgentBase
from reefTracking.reefTracker import ReefTracker
from tools.Constants import CameraExtrinsics, CameraIntrinsics, MapConstants
from tools import UnitConversion
from demos.utils import drawRobotWithCams

class ReefTrackingAgentBase(CameraUsingAgentBase):
    """ Agent -> (CameraUsingAgentBase, PositionLocalizingAgentBase) -> TimestampRegulatedAgentBase -> ReefTrackingAgentBase
        This agent adds reef tracking capabilites. Must be used as partial
        If showFrames is True, you must run this agent as main
    """
    def __init__(self, cameraPath, cameraIntrinsics : CameraIntrinsics, showFrames = False):
        super().__init__(cameraPath, showFrames)
        self.cameraIntrinsics = cameraIntrinsics

    def create(self):
        super().create()
        self.tracker = ReefTracker(cameraIntrinsics=self.cameraIntrinsics,isDriverStation=True)
    
    def runPeriodic(self):
        super().runPeriodic()
        
        coords = self.tracker.getAllTracks(self.latestFrame, drawBoxes=True)
        print(coords)

    def getName(self):
        return "Reef_Tracking_Agent"

    def getDescription(self):
        return "Gets_Reef_State"


def ReefTrackingAgentPartial(
    cameraPath, cameraIntrinsics, showFrames = False
):
    """Returns a partially completed ReefTrackingAgent agent. All you have to do is pass it into neo"""
    return partial(
        ReefTrackingAgentBase,
        cameraPath=cameraPath,
        cameraIntrinsics=cameraIntrinsics,
        showFrames=showFrames
    )