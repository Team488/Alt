from enum import Enum
class DetectionType(Enum):
    REDROBOT = "rrobot"
    BLUEROBOT = "brobot"
    GAMEOBJECT = "gameobj"


def isTypeRobot(type : DetectionType) -> bool:
        return (type == DetectionType.REDROBOT or type == DetectionType.BLUEROBOT)
            