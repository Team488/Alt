from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools.Constants import CameraExtrinsics, CameraIntrinsics
import cv2

from tools.Units import UnitMode


def verifyValidOutput():
    frameProcessor = LocalFrameProcessor(
        CameraIntrinsics.OAKDLITE, CameraExtrinsics.DEPTHLEFT,unitMode=UnitMode.CM
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
