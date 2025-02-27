import cv2
from Core.Agents.Abstract.PathPlanningAgentBase import PathPlanningAgentBase
from Core.Agents.CentralAgentBase import CentralAgentBase
from Core.Orders import TargetUpdatingOrder


class DriveToTargetAgent(CentralAgentBase, PathPlanningAgentBase):
    def create(self) -> None:
        super().create()
        self.targetConf = self.propertyOperator.createProperty("targetMinConf", 0.3)
        self.bestConf = self.propertyOperator.createReadOnlyProperty(
            "bestTarget.bestConf", 0
        )
        self.bestX = self.propertyOperator.createReadOnlyProperty("bestTarget.bestX", 0)
        self.bestY = self.propertyOperator.createReadOnlyProperty("bestTarget.bestY", 0)

    def getPath(self):
        target = self.central.objectmap.getHighestObject(class_idx=1)
        conf = target[2]

        self.bestX.set(float(target[0]))
        self.bestY.set(float(target[1]))
        self.bestConf.set(float(conf))

        path = None
        if conf > self.targetConf.get():
            path = self.central.pathGenerator.generate(
                (self.robotPose2dMRAD[0] * 100, self.robotPose2dMRAD[1] * 100),
                target[:2],
            )
        return path

    def runPeriodic(self) -> None:
        super().runPeriodic()

    def isRunning(self) -> bool:
        return True

    def getName(self) -> str:
        return "Drive_To_Target_Pathplanning"

    def getDescription(self) -> str:
        return "Ingest_Detections_Give_Path"


class DriveToFixedPointAgent(PathPlanningAgentBase):
    def create(self) -> None:
        super().create()
        self.targetX = self.propertyOperator.createProperty(
            propertyName="targetX", propertyDefault=2
        )
        self.targetY = self.propertyOperator.createProperty(
            propertyName="targetY", propertyDefault=2
        )

    def getPath(self):
        target = (self.targetX.get() * 100, self.targetY.get() * 100)
        self.Sentinel.info(f"{self.robotPose2dMRAD=} {target=}")
        return self.central.pathGenerator.generate(
            (self.robotPose2dMRAD[0] * 100, self.robotPose2dMRAD[1] * 100),
            target,
            reducePoints=True,
        )

    def isRunning(self) -> bool:
        return True

    def getName(self) -> str:
        return "Drive_To_FixedPoint_Pathplanning"

    def getDescription(self) -> str:
        return "Get_Target_Give_Path"


class DriveToNetworkTargetAgent(PathPlanningAgentBase):
    def create(self) -> None:
        super().create()
        self.hasTarget = self.propertyOperator.createReadOnlyProperty(
            propertyName="hasTarget", propertyValue=False
        )

    def getPath(self):
        target = self.shareOp.get(TargetUpdatingOrder.TARGETKEY)
        if target == None:
            self.hasTarget.set(False)
            return None
        else:
            self.hasTarget.set(True)

        self.Sentinel.info(f"in meters: {self.robotPose2dMRAD=} {target=}")

        # from meters into cm
        return self.central.pathGenerator.generate(
            (self.robotPose2dMRAD[0] * 100, self.robotPose2dMRAD[1] * 100),
            (target[0] * 100, target[1] * 100),
            reducePoints=True,
        )

    def isRunning(self) -> bool:
        return True

    def getName(self) -> str:
        return "Drive_To_NetworkTarget_Pathplanning"

    def getDescription(self) -> str:
        return "Get_Target_Give_Path"
