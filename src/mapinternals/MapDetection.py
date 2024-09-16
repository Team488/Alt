"""
    Goals for this class

    This will be a simple wrapper. Thats pretty much it. All it will store is, a unique label for the detection, detection probability, an XY coordinate(where the detection was), and extra conditional information on whether
    its a robot or gameobject, what color robot bumper etc
"""
import DetectionType


class MapDetection:
    def __init__(
        self,
        detectionCoords: tuple[int, int],
        detectionType: DetectionType,
        detectionProbablility: float,
        detectionLabel: str,
    ):
        self.detectionCoords = detectionCoords
        self.detectionType = detectionType
        self.detectionProbablilty = detectionProbablility
        self.detectionLabel = detectionLabel
