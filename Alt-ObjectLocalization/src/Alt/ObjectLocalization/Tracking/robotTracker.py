import numpy as np


class RobotTracker:
    tracker = None
    encoder = None
    tracks = None

    def __init__(self) -> None:
        from deep_sort.tracker import Tracker as DeepSortTracker
        from deep_sort_tools import generate_detections as gdet
        from deep_sort import nn_matching

        max_cosine_distance = 0.4
        nn_budget = None

        encoder_model_filename = "assets/mars-small128.pb"

        metric = nn_matching.NearestNeighborDistanceMetric(
            "cosine", max_cosine_distance, nn_budget
        )
        self.tracker = DeepSortTracker(metric)
        self.encoder = gdet.create_box_encoder(encoder_model_filename, batch_size=1)

    def update(self, frame, detections) -> None:
        from deep_sort.detection import Detection

        if len(detections) == 0:
            self.tracker.predict()
            self.tracker.update([])
            self.update_tracks()
            return

        bboxes = np.asarray([d[:-1] for d in detections])
        bboxes[:, 2:] = bboxes[:, 2:] - bboxes[:, 0:2]  # tlbr to tlwh
        scores = [d[-1] for d in detections]

        """ Feature detection 'not enabled' right now, enable this on orin"""
        # features = self.encoder(frame, bboxes) todo get this on a .rknn way too slow currently

        dets = []
        for bbox_id, bbox in enumerate(bboxes):
            dets.append(Detection(bbox, scores[bbox_id], np.ones(128)))

        self.tracker.predict()
        try:
            self.tracker.update(dets)
        except IndexError:
            print(
                "Weird deepsort error that happens once a thousand times. This is here until fixed! -Adem"
            )
        self.update_tracks()

    def update_tracks(self) -> None:
        tracks = []
        for track in self.tracker.tracks:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            bbox = track.to_tlbr()

            id = track.track_id

            tracks.append(RobotTrack(id, bbox, track.currentDetection))

        self.tracks = tracks


class RobotTrack:
    track_id = None
    bbox = None
    currentDetection = None

    def __init__(self, id, bbox, currentDetection) -> None:
        self.track_id = id
        self.bbox = bbox
        self.currentDetection = currentDetection
