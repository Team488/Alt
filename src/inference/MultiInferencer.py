import time
import cv2
import numpy as np
from abstract.inferencerBackend import InferencerBackend
from tools.Constants import ConfigConstants, InferenceMode, Backend
from Core.LogManager import getLogger

Sentinel = getLogger("Multi_Inferencer")


class MultiInferencer:
    def __init__(self, inferenceMode: InferenceMode):
        self.inferenceMode = inferenceMode
        self.backend = self.__getBackend(self.inferenceMode)
        self.backend.initialize()

    def __getBackend(self, inferenceMode: InferenceMode) -> InferencerBackend:
        backend = inferenceMode.getBackend()
        if backend == Backend.RKNN:
            from inference.rknnInferencer import rknnInferencer

            return rknnInferencer(mode=inferenceMode)

        if backend == Backend.ONNX:
            from inference.onnxInferencer import onnxInferencer

            return onnxInferencer(mode=inferenceMode)

        if backend == Backend.ULTRALYTICS:
            from inference.ultralyticsInferencer import ultralyticsInferencer

            return ultralyticsInferencer(mode=inferenceMode)

        Sentinel.fatal(f"Invalid backend provided!: {backend}")
        return None

    def run(self, frame, minConf, drawBoxes=False):
        start = time.time_ns()
        if frame is None:
            Sentinel.fatal("Frame is None!")
            return

        tensor = self.backend.preprocessFrame(frame)
        pre = time.time_ns()
        if tensor is None:
            Sentinel.fatal("Inference Backend preprocessFrame() returned none!")
            return

        prens = pre - start

        results = self.backend.runInference(inputTensor=tensor)
        inf = time.time_ns()
        if results is None:
            Sentinel.fatal("Inference Backend runInference() returned none!")
            return

        infns = inf - pre

        processed = self.backend.postProcess(results, frame, minConf)
        post = time.time_ns()
        if processed is None:
            Sentinel.fatal("Inference Backend postProcess() returned none!")
            return

        postns = post - inf

        totalTimeElapsedNs = prens + infns + postns
        Sentinel.debug(f"{totalTimeElapsedNs=} {prens=} {infns=} {postns}")
        cumulativeFps = 1e9 / totalTimeElapsedNs

        # do stuff here
        if drawBoxes:
            cv2.putText(
                frame, f"FPS: {cumulativeFps}", (10, 20), 1, 1, (255, 255, 255), 1
            )

            for (bbox, conf, class_id) in processed:
                # try to get label
                label = f"Id out of range!: {class_id}"
                if len(self.backend.labels) > class_id:
                    label = self.backend.labels[class_id]

                p1 = tuple(map(int, bbox[:2]))  # Convert to integer tuple
                p2 = tuple(map(int, bbox[2:4]))  # Convert to integer tuple
                m = tuple(map(int, np.add(bbox[:2], bbox[2:4]) / 2))
                cv2.rectangle(frame, p1, p2, (0, 0, 255), 3)  # Drawing the rectangle
                cv2.putText(
                    frame, f"Label: {label} Conf: {conf:.2f}", m, 1, 1, (0, 255, 0), 1
                )

        return processed
