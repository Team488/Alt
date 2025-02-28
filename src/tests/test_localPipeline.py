from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools.Constants import (
    ColorCameraExtrinsics2024,
    CameraIntrinsicsPredefined,
    InferenceMode,
)
import cv2

from tools.Units import UnitMode


def verifyValidOutput() -> None:
    frameProcessor = LocalFrameProcessor(
        CameraIntrinsicsPredefined.OAKDLITE4K,
        ColorCameraExtrinsics2024.DEPTHLEFT,
        inferenceMode=InferenceMode.ONNX2024,
    )  # these are not needed for the test
    cap = cv2.VideoCapture("assets/video12qual25clipped.mp4")
    cap.set(cv2.CAP_PROP_POS_FRAMES, 768)
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        count += 1
        print(count)
        if ret:
            out = frameProcessor.processFrame(frame)
            if out:
                print(out)
        cv2.imshow("frame", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# verifyValidOutput()
