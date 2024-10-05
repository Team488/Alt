from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools.Constants import CameraIntrinsics, CameraExtrinsics
import cv2


def startDemo():
    cameraExtr = CameraExtrinsics.DEPTHLEFT
    cameraIntr = CameraIntrinsics.OAKDLITE
    cap = cv2.VideoCapture("assets/video12qual25clipped.mp4")
    firstRun = True
    frameProcessor = LocalFrameProcessor(cameraIntr, cameraExtr)

    while cap.isOpened():
        ret, frame = cap.read()
        if firstRun:
            firstRun = False
        if ret:
            # Run YOLOv8 on the frame
            out = frameProcessor.processFrame(frame)

            # Run YOLOv8 on the frame
            for result in out:
                id = result[0]
                x, y, z = result[1]
                conf = result[2]
                isRobot = result[3]
                # here are results
        else:
            break

    cap.release()
    cv2.destroyAllWindows()
