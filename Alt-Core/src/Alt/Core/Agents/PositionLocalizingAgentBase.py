from typing import Tuple, Any

from .Agent import AgentBase
from ..Utils import NtUtils


class PositionLocalizingAgentBase(AgentBase):
    """Agent -> PositionLocalizingAgentBase

    Extending Agent with Localizing capabilites. Supports only XTables
    NOTE: For changes to properties to take place, the Agent must be restarted
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        # Initialize robot pose variables
        self.robotPose2dMRAD: Tuple[float, float, float] = (0, 0, 0)
        self.robotPose2dCMRAD: Tuple[float, float, float] = (0, 0, 0)
        self.connectedToLoc: bool = False
        self.locTimeStamp: int = -1

    def create(self) -> None:
        if self.propertyOperator is None:
            raise ValueError("PropertyOperator not initialized")

        if self.xclient is None:
            raise ValueError("XTablesClient not initialized")

        # create managing properties
        self.xtablesPosTable = self.propertyOperator.createProperty(
            propertyTable="xtablesPosTable", propertyDefault="PoseSubsystem.RobotPose"
        )

        self.locX = self.propertyOperator.createReadOnlyProperty("Robot.Robot_Loc_X", 0)
        self.locY = self.propertyOperator.createReadOnlyProperty("Robot.Robot_Loc_Y", 0)
        self.locRot = self.propertyOperator.createReadOnlyProperty("Robot.Robot_Rot", 0)

        self.positionOffsetXM = self.propertyOperator.createProperty(
            "Position_Offset_X_M", propertyDefault=0, loadIfSaved=False
        )
        self.positionOffsetYM = self.propertyOperator.createProperty(
            "Position_Offset_Y_M", propertyDefault=0, loadIfSaved=False
        )
        self.positionOffsetYAWDEG = self.propertyOperator.createProperty(
            "Position_Offset_YAW_Deg", propertyDefault=0, loadIfSaved=False
        )

        # Variable to store robot location. Units will be (X(m), Y(m), Yaw Rotation (rad))
        self.robotPose2dMRAD = (0, 0, 0)
        self.robotPose2dCMRAD = (0, 0, 0)
        self.connectedToLoc = False
        self.locTimeStamp = -1

        self.xclient.subscribe(self.xtablesPosTable.get(), self.__updateLocation)

    def __updateLocation(self, ret: Any) -> None:
        if self.Sentinel is None:
            return

        try:
            self.robotPose2dMRAD = NtUtils.getPose2dFromBytes(ret.value)
            self.robotPose2dCMRAD = (
                self.robotPose2dMRAD[0] * 100,
                self.robotPose2dMRAD[1] * 100,
                self.robotPose2dMRAD[2],
            )  # m to cm

            if self.locX and self.locY and self.locRot:
                self.locX.set(self.robotPose2dMRAD[0])
                self.locY.set(self.robotPose2dMRAD[1])
                self.locRot.set(self.robotPose2dMRAD[2])

            # self.Sentinel.debug("Updated robot pose!!")
            self.connectedToLoc = True
        except Exception as e:
            self.Sentinel.debug(e)
            self.Sentinel.debug("Could not get robot pose!!")
            self.connectedToLoc = False
