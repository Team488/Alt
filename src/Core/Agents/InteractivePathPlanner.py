# from typing import Any, Optional
# import cv2
# import numpy as np
# from Core.Agents.Abstract.PathPlanningAgentBase import PathPlanningAgentBase
# from Core.Agents.CentralAgent import CentralAgent
# from tools import UnitConversion


# class InteractivePathPlanner(CentralAgent, PathPlanningAgentBase):
#     """Agent -> LocalizingAgentBase -> PathPlanningAgentBase -> InteractivePathPlanner

#     NOTE: due to the nature of opencv, this agent must be run on main thread
#     """

#     def create(self) -> None:
#         super().create()
#         self.tx = self.propertyOperator.createReadOnlyProperty("currentTargetX", 0)
#         self.ty = self.propertyOperator.createReadOnlyProperty("currentTargetY", 0)
#         cv2.namedWindow("pathplanner")
#         self.target = (0, 0)
#         cv2.setMouseCallback("pathplanner", self.__updateTarget)
#         self.runFlag = True

#     def __updateTarget(self, event, x, y, flags, param) -> None:
#         if event == cv2.EVENT_LBUTTONDOWN:
#             # invert y
#             y = int(UnitConversion.invertY(y))
#             self.target = (x, y)
#             self.tx.set(x)
#             self.ty.set(y)

#     def getPath(self) -> Optional[list[tuple[int, int]]]:
#         return self.central.pathGenerator.generateToPointWStaticRobots(
#             (self.robotPose2dMRAD[0] * 100, self.robotPose2dMRAD[1] * 100),
#             self.target[:2],
#         )

#     def isRunning(self) -> bool:
#         return self.runFlag

#     def getName(self) -> str:
#         return "Click_To_Target_Pathplanning"

#     def getDescription(self) -> str:
#         return "Click_Where_To_Go"
