import numpy as np
from deep_sort.tracker import Tracker as DeepSortTracker
from deep_sort_tools import generate_detections as gdet
from deep_sort import nn_matching
from deep_sort.detection import Detection

from Alt.Core import getChildLogger, ISARM64

Sentinel = getChildLogger("Object_Tracker")

class RobotTracker:
    tracker = None
    encoder = None
    tracks = None

    def __init__(self) -> None:
        # TODO parametrize these as inputs (ie should depend on the object)

        max_cosine_distance = 0.4
        nn_budget = None

        encoder_model_filename = "assets/mars-small128.pb"

        metric = nn_matching.NearestNeighborDistanceMetric(
            "cosine", max_cosine_distance, nn_budget
        )
        self.tracker = DeepSortTracker(metric)
        self.encoder = gdet.create_box_encoder(encoder_model_filename, batch_size=1)

    def update(self, frame, detections) -> None:

        if len(detections) == 0:
            self.tracker.predict()
            self.tracker.update([])
            self.update_tracks()
            return

        bboxes = np.asarray([d[:-1] for d in detections])
        bboxes[:, 2:] = bboxes[:, 2:] - bboxes[:, 0:2]  # tlbr to tlwh
        scores = [d[-1] for d in detections]

        """ Feature extraction disabled on arm64 rn, as its too slow on smaller devices. TODO speed up, with conversions to .rknn or such"""

        if not ISARM64:
            features = self.encoder(frame, bboxes)
        else:
            # giving ranndom feature for now
            features = [np.random.rand(128) for _ in bboxes]

        dets = []
        for bbox_id, bbox in enumerate(bboxes):
            dets.append(Detection(bbox, scores[bbox_id], features[bbox_id]))

        self.tracker.predict()
        try:
            self.tracker.update(dets)
        except IndexError as e:
            Sentinel.debug(f"Weird deepsort error that happens once a thousand times.\n{e}")
            return

        self.update_tracks()

    def update_tracks(self) -> None:
        tracks = []
        for track in self.tracker.tracks:
            if not track.is_confirmed() or track.time_since_update > 1:
                continue
            bbox = track.to_tlbr()

            tracks.append(RobotTrack(track.track_id, bbox, track.currentDetection))

        self.tracks = tracks


class RobotTrack:
    track_id = None
    bbox = None
    currentDetection = None

    def __init__(self, track_id, bbox, currentDetection) -> None:
        self.track_id = track_id
        self.bbox = bbox
        self.currentDetection = currentDetection
