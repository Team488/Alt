from abstract.Agent import Agent
from tools import NtUtils


class PositionLocalizingAgentBase(Agent):
    """Agent -> PositionLocalizingAgentBase

    Extending Agent with Localizing capabilites. Supports only XTables
    NOTE: For changes to properties to take place, the Agent must be restarted
    """

    def create(self) -> None:
        super().create()
        # create managing properties
        self.xtablesPosTable = self.propertyOperator.createProperty(
            propertyTable="xtablesPosTable", propertyDefault="PoseSubsystem.RobotPose"
        )

        self.locX = self.propertyOperator.createReadOnlyProperty("Robot.Robot_Loc_X", 0)
        self.locY = self.propertyOperator.createReadOnlyProperty("Robot.Robot_Loc_Y", 0)
        self.locRot = self.propertyOperator.createReadOnlyProperty("Robot.Robot_Rot", 0)

        """Variable to store robot location. Units will be (X(m), Y(m), Yaw Rotation (rad))"""
        self.robotPose2dMRAD = (0, 0, 0)
        self.robotPose2dCMRAD = (0, 0, 0)
        self.connectedToLoc = False
        self.locTimeStamp = -1

        self.xclient.subscribe(self.xtablesPosTable.get(), self.__updateLocation)

    def __updateLocation(self, ret) -> None:
        try:
            self.robotPose2dMRAD = NtUtils.getPose2dFromBytes(ret.value)
            self.robotPose2dCMRAD = (
                self.robotPose2dMRAD[0] * 100,
                self.robotPose2dMRAD[1] * 100,
                self.robotPose2dMRAD[2],
            )  # m to cm

            self.locX.set(self.robotPose2dMRAD[0])
            self.locY.set(self.robotPose2dMRAD[1])
            self.locRot.set(self.robotPose2dMRAD[2])
            # self.Sentinel.debug("Updated robot pose!!")
            self.connectedToLoc = True
        except Exception as e:
            self.Sentinel.debug(e)
            self.Sentinel.debug("Could not get robot pose!!")
            self.connectedToLoc = False
