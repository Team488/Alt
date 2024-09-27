from mapinternals.robotTracker import RobotTracker

class DeepSortBaseLabler:
    def __init__(self) -> None:
        self.trackerGameObjects = RobotTracker()
        self.trackerRobots = RobotTracker()

    """ Returns list of tracked ids, with id, bbox, conf, isRobot?"""

    def getLocalLabels(
        self, frame, results
    ) -> list[tuple[int, tuple[int, int, int, int], float, bool]]:
        trackedDetections = []
        if not results:
            return trackedDetections
        for result in results:
            savedScores = {}
            detectionsGameObjects = []
            detectionsRobots = []
            for r in result.boxes.data.tolist():
                x1, y1, x2, y2, score, class_id = r
                x1 = int(x1)
                x2 = int(x2)
                y1 = int(y1)
                y2 = int(y2)
                class_id = int(class_id)
                detection = [x1, y1, x2, y2, score]
                bbox = (x1, y1, x2, y2)
                savedScores[bbox] = score
                if class_id == 0:  # robot
                    detectionsRobots.append(detection)
                else:
                    detectionsGameObjects.append(detection)
            self.trackerGameObjects.update(frame, detectionsGameObjects)
            self.trackerRobots.update(frame, detectionsRobots)
            for track in self.trackerRobots.tracks:
                # bbox = track.bbox
                # x1, y1, x2, y2 = bbox
                trackedDetections.append(
                    (track.track_id, bbox, savedScores.get(bbox, 0), True)
                )  # should never hit default case
            for track in self.trackerGameObjects.tracks:
                # bbox = track.bbox
                # x1, y1, x2, y2 = bbox
                trackedDetections.append(
                    (
                        track.track_id,
                        bbox,
                        savedScores.get(bbox, 0),
                        False,
                    )
                )
        return trackedDetections
