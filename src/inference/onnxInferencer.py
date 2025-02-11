import cv2
import numpy as np
import onnxruntime as ort
from inference import utils
from abstract.inferencerBackend import InferencerBackend
from tools.Constants import ConfigConstants, InferenceMode
from Core import Neo

Sentinel = Neo.getLogger("onnx_inferencer")
class onnxInferencer(InferencerBackend):

    def initialize(self):
        providers = ort.get_available_providers()
        Sentinel.info(f"Using provider {providers[0]}")
        session_options = ort.SessionOptions()
        self.session = ort.InferenceSession(
            self.mode.getModelPath(), sess_options=session_options,providers=providers
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

    def postProcess(self, results, frame, minConf):
        adjusted = self.adjustBoxes(results[0], frame.shape, minConf)
        nmsResults = utils.non_max_suppression(adjusted, minConf)
        return nmsResults
        

def startDemo():
    video_path = "assets/reefscapevid.mp4"
    cap = cv2.VideoCapture(video_path)
    inferencer = onnxInferencer(model_path="assets/2025-best-151.onnx")
    # Check if the video opened successfully
    if not cap.isOpened():
        print("Error: Could not open video.")
        exit()

    cap.set(cv2.CAP_PROP_POS_FRAMES, 1004)

    # Process each frame
    while True:
        ret, frame = cap.read()
        if ret:
            inferencer.inferenceFrame(frame, drawBox=True)
            cv2.imshow("frame", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cv2.destroyAllWindows()
    cap.release

if __name__ == "__main__":
    startDemo()