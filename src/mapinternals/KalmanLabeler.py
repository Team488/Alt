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
from deep_sort.tracker import Tracker


class KalmanLabeler:
    def __init__(self):
        # here put all persistent data
        self.trackerNotes = Tracker()
        self.trackerRobots = Tracker()
        self.detectionThreshold = 0.7
        kalmanData = {}  # example

    def getLocalLabels(self, frame, results):
        if not results:
            return ()
        trackIds = ()
        for result in results:
            detectionsNotes = []
            detectionsRobots = []
            for r in result.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = r
                x1 = int(x1)
                x2 = int(x2)
                y1 = int(y1)
                y2 = int(y2)
                class_id = int(class_id)
                detection = [x1, y1, x2, y2, score]
                if class_id == 0:  # robot
                    detectionsRobots.append(detection)
                else:
                    detectionsNotes.append(detection)
            self.trackerNotes.update(frame, detectionsNotes)
            self.trackerRobots.update(frame, detectionsRobots)
            for track in self.trackerRobots.tracks:
                # bbox = track.bbox
                # x1, y1, x2, y2 = bbox
                trackIds.append(track.track_id)
            for track in self.trackerNotes.tracks:
                # bbox = track.bbox
                # x1, y1, x2, y2 = bbox
                trackIds.append(track.track_id)
        return trackIds
