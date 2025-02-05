from abstract.PathPlanningAgentBase import PathPlanningAgentBase
from abstract.CentralAgentBase import CentralAgentBase

class DriveToTargetAgent(CentralAgentBase,PathPlanningAgentBase):
    def create(self):
        super().create()
        self.targetConf = self.propertyOperator.createProperty("targetMinConf", 0.3)
        self.bestConf = self.propertyOperator.createReadOnlyProperty(
            "currentTargetBestConf", 0
        )

    def getPath(self):
        target = self.central.map.getHighestGameObject()
        conf = target[2]
        self.bestConf.set(float(conf))
        path = None
        if conf > self.targetConf.get():
            path = self.central.pathGenerator.generate(
                (self.robotLocation[0] * 100, self.robotLocation[1] * 100), target[:2]
            )
        return path

    def isRunning(self):
        return True

    @staticmethod
    def getName():
        return "PathPlanning_Agent"

    @staticmethod
    def getDescription():
        return "Ingest_Detections_Give_Path"



class DriveToFixedPointAgent(PathPlanningAgentBase):
    def create(self):
        super().create()
        self.targetX = self.propertyOperator.createProperty(
            propertyName="targetX", propertyDefault=2
        )
        self.targetY = self.propertyOperator.createProperty(
            propertyName="targetY", propertyDefault=2
        )

    def getPath(self):
        target = (self.targetX.get() * 100, self.targetY.get() * 100)
        self.Sentinel.info(f"{target=}")
        self.Sentinel.info(f"{self.robotLocation=} {target=}")
        return self.central.pathGenerator.generate((self.robotLocation[0] * 100, self.robotLocation[1] * 100), target)

    def isRunning(self):
        return True

    @staticmethod
    def getName():
        return "PathPlanning_Agent"

    @staticmethod
    def getDescription():
        return "Ingest_Detections_Give_Path"
