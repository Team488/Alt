import cv2
import numpy as np
from abstract.PathPlanningAgentBase import PathPlanningAgentBase
from abstract.CentralAgentBase import CentralAgentBase


class InteractivePathPlanner(CentralAgentBase, PathPlanningAgentBase):
    """ Agent -> LocalizingAgentBase -> PathPlanningAgentBase -> InteractivePathPlanner

        NOTE: due to the nature of opencv, this agent must be run on main thread 
     """
    def create(self):
        super().create()
        self.tx = self.propertyOperator.createReadOnlyProperty(
            "currentTargetX", 0
        )
        self.ty = self.propertyOperator.createReadOnlyProperty(
            "currentTargetY", 0
        )
        cv2.namedWindow("pathplanner")
        self.target = (0,0)
        cv2.setMouseCallback("pathplanner",self.__updateTarget)
        self.runFlag = True

    def __updateTarget(self, event, x, y, flags, param):
        if event == cv2.EVENT_LBUTTONDOWN:
            self.target = (x,y)
            self.tx.set(x)
            self.ty.set(y)
    
    def getPath(self):
        return self.central.pathGenerator.generate(
            (self.robotLocation[0] * 100 + 1, self.robotLocation[1] * 100 + 1),
            self.target[:2],
        )

    def runPeriodic(self):
        super().runPeriodic()
        frame = cv2.merge((self.central.map.getGameObjectHeatMap(),np.zeros_like(self.central.map.getGameObjectHeatMap()),self.central.map.getRobotHeatMap()))
        cv2.putText(frame,"Game Objects: Blue | Robots : Red | Path : White",(10,20),0,1,(255,255,255),2)
        if self.path:
            for point in self.path:
                cv2.circle(frame, tuple(map(int,point)), 5, (255,255,255), -1)
        cv2.imshow("pathplanner", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            self.runFlag = False

    def isRunning(self):
        return self.runFlag

    @staticmethod
    def getName():
        return "Click_To_Target_Pathplanning"

    @staticmethod
    def getDescription():
        return "Click_Where_To_Go"


