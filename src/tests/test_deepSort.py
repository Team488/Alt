from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools.Constants import CameraExtrinsics, CameraIntrinsics
import cv2


def show_featureType():
    frameProcessor = LocalFrameProcessor(
        CameraIntrinsics.OAKDLITE, CameraExtrinsics.DEPTHLEFT
    )  # these are not needed for the test
    cap = cv2.VideoCapture("assets/video12qual25clipped.mp4")
    cap.set(cv2.CAP_PROP_POS_FRAMES, 768)
    count = 0
    while cap.isOpened():
        ret, frame = cap.read()
        count += 1  # why no ++count or count++ :(
        print(count)
        if ret:
            out = frameProcessor.processFrame(frame)
            if out:
                features = out[0][-1]
                print(features)
                print(type(features))
                break

        cv2.imshow("frame", frame)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# show_featureType()
