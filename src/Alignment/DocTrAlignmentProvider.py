from collections import defaultdict
import cv2
import io
import re
import time
from PIL import Image
import numpy as np
from abstract.AlignmentProvider import AlignmentProvider
from Core import PropertyOperator, getChildLogger
from doctr.models import ocr_predictor
from doctr.io import DocumentFile
from doctr.utils.geometry import detach_scores

Sentinel = getChildLogger("DocTr_Alignment_Provider")


class DocTrAlignmentProvider(AlignmentProvider):
    def __init__(self):
        super().__init__()
        self.initalizerDetector()

    def initalizerDetector(self):
        self.ocr_predictor = ocr_predictor(
            "fast_tiny",
            pretrained=True,
            assume_straight_pages=False,
            preserve_aspect_ratio=True,
            resolve_blocks=True,
        )  # .cuda().half()  # Uncomment this line if you have a GPU

        # Define the postprocessing parameters (optional)
        self.ocr_predictor.det_predictor.model.postprocessor.bin_thresh = 0.3
        self.ocr_predictor.det_predictor.model.postprocessor.box_thresh = 0.1

    def isColorBased(self):
        return False  # uses april tags so b/w frame

    def align(self, inputFrame, draw):
        received_frame = time.time()
        Sentinel.info(f"Received Time: {received_frame}")
        frame = inputFrame  # move og ref of input frame to draw on original
        if not self.checkFrame(frame):
            # we assume if its not a b/w frame (eg checkframe false), that it means its a cv2 bgr and to change to b/w
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        frame = cv2.cvtColor(frame, cv2.COLOR_GRAY2RGB)

        results = self.ocr_predictor([frame])
        left = None
        right = None
        if results is not None:
            Sentinel.info(f"Found results from doctr: {results}")
            Sentinel.info(f"results export: {results.export()}")

        processed_frame = time.time()
        Sentinel.info(f"Processed Time: {processed_frame}")
        if len(results.pages) < 1:
            return None, None

        for doc, res in zip(frame, results.pages[0].blocks):
            img_shape = results.pages[0].dimensions
            matched_words = list(
                filter(
                    lambda word: word.value is not None
                    and (word.value.startswith("ID") or re.search(word.value, r"\d+$")),
                    [word for line in res.lines for word in line.words],
                )
            )
            if matched_words is None or len(matched_words) == 0:
                continue

            for word in matched_words:
                for coords in word.geometry:
                    Sentinel.info(f"coords: {coords}")

                    # Convert relative to absolute pixel coordinates
                    points = np.array(
                        self._to_absolute([coords], img_shape), dtype=np.int32
                    )
                    Sentinel.info(f"points: {points}")
                    Sentinel.info(f"draw: {draw}")

                    if draw:
                        cv2.polylines(
                            inputFrame,
                            [points],
                            isClosed=True,
                            color=(255, 0, 0),
                            thickness=2,
                        )

                    point_list = points.tolist()
                    if len(point_list) > 0:
                        left = left if left is not None else point_list[0][0]
                        right = right if right is not None else point_list[0][0]

                        vals = [point[0] for point in point_list]
                        Sentinel.info(f"vals: {vals}")
                        vals.append(left)
                        vals.append(right)
                        left = min(vals)
                        right = max(vals)

        Sentinel.info("Left: " + str(left) + " Right: " + str(right))

        return left, right

    # Helper function to convert relative coordinates to absolute pixel values
    def _to_absolute(
        self, coords: list[tuple[float, float]], img_shape: tuple[int, int]
    ) -> list[list[int]]:
        h, w = img_shape
        return [[int(point[0] * w), int(point[1] * h)] for point in coords]
