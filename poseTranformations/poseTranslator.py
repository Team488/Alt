import math
from enum import Enum
from typing import Tuple, Union, Optional

class cameraLocation(Enum):
    # see diagram attached
    # https://xbot.slack.com/archives/C8NPFHU6M/p1707160615692579
    TOPLEFT = (-10,-10)
    TOPRIGHT = (10,-10)
    BOTTOMLEFT = (-10,-10)
    BOTTOMRIGHT = (-10,-10)
    # todo find these values!

class poseTranslator:
    def __init__(self) -> None:
        pass
    
    def worldToRobotPose(self, x: float, y: float, z: float = 0) -> float:
        return -10
    
    def robotToWorldPose(self, x: float, y: float, z: float = 0) -> float:
        return -10
    
    def bearingAndDistanceToXY(self, yaw: float, length: float) -> Tuple[float, float]:
        x = math.cos(yaw)*length
        z = math.sin(yaw)*length

        return x, z
    


transl = poseTranslator()
x,z = transl.bearingAndDistanceToXY(-math.pi/10,20)
print(f"X: {x}\nZ: {z}")
