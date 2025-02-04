from networktables import NetworkTables
from abstract.Agent import Agent
from tools import NtUtils


class LocalizingAgentBase(Agent):
    """ Agent -> LocalizingAgentBase

        Extending Agent with Localizing capabilites. Supports both NetworkTables And XTables
        NOTE (NetworkTables Only): For changes to properties to take place, the Agent must be restarted
    """
    def create(self):        
        super().create()
        # create managing properties
        self.xtablesPosTable = self.propertyOperator.createProperty(
            propertyName="xtablesPosTable", propertyDefault="PoseSubsystem.RobotPose"
        )
        self.ntPosTable = self.propertyOperator.createProperty(
            propertyName="networkTablesPosTable",
            propertyDefault="AdvantageKit/RealOutputs/PoseSubsystem/RobotPose",
        )
        self.useXTables = self.propertyOperator.createProperty(
            propertyName="useXtablesForPosition", propertyDefault=True
        )
        # do some networktables preinit
        NetworkTables.initialize(server="10.4.88.2")
        posePath: str = self.ntPosTable.get()
        entryIdx = posePath.rfind("/")
        poseTable = posePath[:entryIdx]
        poseEntry = posePath[entryIdx + 1 :]
        table = NetworkTables.getTable(poseTable)
        self.ntpos = table.getEntry(poseEntry)

        """Variable to store robot location. Units will be (X(m), Y(m), Yaw Rotation (rad))"""
        self.robotLocation = (0,0,0)

    
    def __updateLocation(self):
        if self.useXTables.get():
            posebytes = self.xclient.getUnknownBytes(self.xtablesPosTable.get())
        else:
            posebytes = self.ntpos.get()
        if posebytes:
            self.robotLocation = NtUtils.getPose2dFromBytes(posebytes)
        else:
            self.Sentinel.warning("Could not get robot pose!!")

    def runPeriodic(self):
        super().runPeriodic()
        self.__updateLocation()

