from abstract.Agent import Agent
from tools import NtUtils


class LocalizingAgentBase(Agent):
    """ Agent -> LocalizingAgentBase

        Extending Agent with Localizing capabilites. Supports only XTables
        NOTE: For changes to properties to take place, the Agent must be restarted
    """
    def create(self):        
        super().create()
        # create managing properties
        self.xtablesPosTable = self.propertyOperator.createProperty(
            propertyName="xtablesPosTable", propertyDefault="PoseSubsystem.RobotPose"
        )

        """Variable to store robot location. Units will be (X(m), Y(m), Yaw Rotation (rad))"""
        self.robotLocation = (0,0,0)

        self.xclient.subscribe(self.xtablesPosTable.get(),self.__updateLocation)

    
    def __updateLocation(self, ret):
        try:
            self.robotLocation = NtUtils.getPose2dFromBytes(ret.value)
            self.Sentinel.info("Updated robot pose!!")
        except Exception as e:
            self.Sentinel.debug(e)
            self.Sentinel.warning("Could not get robot pose!!")


