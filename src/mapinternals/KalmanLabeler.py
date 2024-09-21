""" Goals for this class

    Known data: XYCoordinate of new Detection, Detection Type(Robot/Game Object), (If Robot then bumper color), and previous maps

    Goals: Take the new information given, and assign the new detection a label, this label will persist throught detections
    Ex: given new red robot detection at coord (100,121) -> figure out that this is the same robot that was at position (80,80) on the previous map. We use the SAME label so if in our cache it was called
    robot#2, then this will also be robot#2

    Expected output: A Label String that will help us know which robot is which

"""
import DetectionType
import MapDetection
import KalmanCache
import main
import probmap


class KalmanLabeler:
    def __init__(self):
        # here put all persistent data
        kalmanData = {}  # example

    def createDetection(
        self,
        detectionC: tuple[int, int],
        detectionType: DetectionType,
        detectionProb: float,
    ) -> MapDetection:
        # here you will do all of the calculations to assign the new detection

        # will need the current probmap view
        currentMap = None
        if DetectionType.isTypeRobot(detectionType):
            currentMap = main.mapWrapper.getRobotMap()
        else:
            currentMap = main.mapWrapper.getGameObjectMap()

        # now you have the map, all you need to get is the velocity (not sure how will implement for now)

        vel = somewhere.somemethodtogetvelocitybasedoninfo()

        # do your magic here (find which original coordinate on the previous map, this new detection you think came from):

        oldCoords = thing  # find this

        # now once you have figured out where it came from, use the kalman cache and retrieve the label

        label = KalmanCache.somemethodtodothis(oldCoords)

        # now return a boxed MapDetection object now that you have everything
        return MapDetection.MapDetection(
            detectionC, detectionType, detectionProb, label
        )
