import cv2
import numpy as np
import onnxruntime as ort
from inference import utils

class onnxInferencer:
    def __init__(
        self,
        model_path="assets/bestV5.onnx",
        setParallel = False
    ):
        providers = ort.get_available_providers()
        print(f"Using provider {providers[0]}")
        session_options = ort.SessionOptions()
        if setParallel:
            session_options.execution_mode = ort.ExecutionMode.ORT_PARALLEL
        self.session = ort.InferenceSession(
            model_path, sess_options=session_options,providers=providers
        )


    def inferenceFrame(self, frame, conf_threshold=0.4, drawBox=True):
        # Preprocess the frame if needed (resize, normalize, etc.)
        input_frame = utils.letterbox_image(frame.copy())
        # Convert from HWC (height, width, channels) to CHW (channels, height, width)
        input_frame = np.transpose(input_frame, (2, 0, 1))
        input_frame = np.expand_dims(input_frame, axis=0)  # Add batch dimension
        input_frame = input_frame.astype(np.float32)  # Ensure correct data type
        input_frame /= 255
        # Get input/output names from the ONNX model
        input_name = self.session.get_inputs()[0].name
        output_name = self.session.get_outputs()[0].name

        predictions = self.session.run([output_name], {input_name: input_frame})[0]
        adjusted = utils.adjustBoxes(predictions, frame.shape, conf_threshold)
        nmsResults = utils.non_max_suppression(adjusted, conf_threshold)

        # do stuff here
        if drawBox:
            labels = ["robot", "note"]
            for (bbox, conf, class_id) in nmsResults:
                p1 = tuple(map(int, bbox[:2]))  # Convert to integer tuple
                p2 = tuple(map(int, bbox[2:4]))  # Convert to integer tuple
                cv2.rectangle(frame, p1, p2, (0, 255, 0), 1)  # Drawing the rectangle
                cv2.putText(frame, labels[class_id], p1, 1, 2, (0, 255, 0), 1)
        return nmsResults


def startDemo():
    video_path = "assets/video12qual25clipped.mp4"
    cap = cv2.VideoCapture(video_path)
    inferencer = onnxInferencer()
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