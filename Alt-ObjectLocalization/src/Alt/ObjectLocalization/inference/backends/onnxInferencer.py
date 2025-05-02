import cv2
import numpy as np
import onnxruntime as ort

from Alt.Core import getChildLogger

from ...inference import utils
from ..inferencerBackend import InferencerBackend
from ...Detections.DetectionResult import DetectionResult

Sentinel = getChildLogger("onnx_inferencer")


class onnxInferencer(InferencerBackend):
    def initialize(self) -> None:
        providers = ort.get_available_providers()
        Sentinel.info(f"Using provider {providers[0]}")
        session_options = ort.SessionOptions()
        self.session = ort.InferenceSession(
            self.modelConfig.getPath(), sess_options=session_options, providers=providers
        )
        # Get input/output names from the ONNX model
        self.inputName = self.session.get_inputs()[0].name
        self.outputName = self.session.get_outputs()[0].name

    def preprocessFrame(self, frame):
        input_frame = utils.letterbox_image(frame.copy())
        # Convert from HWC (height, width, channels) to CHW (channels, height, width)
        input_frame = np.transpose(input_frame, (2, 0, 1))
        input_frame = np.expand_dims(input_frame, axis=0)  # Add batch dimension
        input_frame = input_frame.astype(np.float32)  # Ensure correct data type
        input_frame /= 255
        return input_frame

    def runInference(self, inputTensor):
        return self.session.run([self.outputName], {self.inputName: inputTensor})

    def postProcessBoxes(self, results, frame, minConf) -> list[DetectionResult]:
        adjusted = self.adjustBoxes(results[0], frame.shape, minConf)
        nmsResults = utils.non_max_suppression(adjusted, minConf)

        return [DetectionResult(nmsResult[0], nmsResult[1], nmsResult[2]) for nmsResult in nmsResults]


def startDemo() -> None:
    from inference.MultiInferencer import MultiInferencer
    from tools.Constants import InferenceMode

    inf = MultiInferencer(inferenceMode=InferenceMode.ONNXMEDIUM2025)
    cap = cv2.VideoCapture("assets/reefscapevid.mp4")

    while cap.isOpened():
        ret, frame = cap.read()
        if ret:
            results = inf.run(frame, 0.7, drawBoxes=True)
            cv2.imshow("onnx", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break


if __name__ == "__main__":
    startDemo()
