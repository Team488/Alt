from functools import partial
import math

import cv2
import numpy as np

from Core.Agents.Abstract.TimestampRegulatedAgentBase import TimestampRegulatedAgentBase
from reefTracking.reefTracker import ReefTracker
from tools.Constants import CameraExtrinsics, CameraIntrinsics, MapConstants
from tools import UnitConversion
from demos.utils import drawRobotWithCams

class ReefTrackingAgentBase(TimestampRegulatedAgentBase):
    """ Agent -> (CameraUsingAgentBase, PositionLocalizingAgentBase) -> TimestampRegulatedAgentBase -> ReefTrackingAgentBase
        This agent adds reef tracking capabilites. Must be used as partial
        If showFrames is True, you must run this agent as main
    """
    def __init__(self, cameraPath, cameraIntrinsics : CameraIntrinsics, cameraExtrinsics : CameraExtrinsics, showFrames = False):
        super().__init__(cameraPath, showFrames)
        self.cameraIntrinsics = cameraIntrinsics
        self.cameraExtrinsics = cameraExtrinsics

    def create(self):
        super().create()
        self.tracker = ReefTracker(cameraIntrinsics=self.cameraIntrinsics,cameraExtrinsics=self.cameraExtrinsics,isDriverStation=False)
    
    def runPeriodic(self):
        super().runPeriodic()
        
        pose2dCMRad = (self.robotPose2dMRAD[0]*100,self.robotPose2dMRAD[1]*100,self.robotPose2dMRAD[2]) # m to cm
        
        coords = self.tracker.getAllTracks(self.latestFrame, pose2dCMRad, drawBoxes=True)
        print(coords)
        # print(coords)
        frame = np.zeros((int(MapConstants.fieldHeight.getCM()),int(MapConstants.fieldWidth.getCM()),3),dtype=np.uint8)
        


        # draw reefs
        cv2.circle(frame,UnitConversion.toint(MapConstants.b_reef_center.getCM()),int(MapConstants.reefRadius.getCM()),(255,0,0),1)
        cv2.circle(frame,UnitConversion.toint(MapConstants.r_reef_center.getCM()),int(MapConstants.reefRadius.getCM()),(0,0,255),1)


        drawRobotWithCams(frame,MapConstants.robotWidth.getCM(),MapConstants.robotHeight.getCM(),pose2dCMRad[0],pose2dCMRad[1],pose2dCMRad[2],[(self.cameraExtrinsics,self.cameraIntrinsics)],cameraLineLength=500)
        frame = cv2.flip(frame,0)
        c = 20
        for key,coord in coords.items():
            cv2.putText(frame, f"Key: {key}", (10,c),1,1,(255,255,255),1)
            c+=20
        cv2.imshow("robot_visualization",frame)

    def getName(self):
        return "Reef_Tracking_Agent"

    def getDescription(self):
        return "Gets_Reef_State"


def ReefTrackingAgentPartial(
    cameraPath, cameraIntrinsics, cameraExtrinsics, showFrames = False
):
    """Returns a partially completed ReefTrackingAgent agent. All you have to do is pass it into neo"""
    return partial(
        ReefTrackingAgentBase,
        cameraPath=cameraPath,
        cameraIntrinsics=cameraIntrinsics,
        cameraExtrinsics=cameraExtrinsics,
        showFrames=showFrames
    )