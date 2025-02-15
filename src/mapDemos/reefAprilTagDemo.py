import cv2
import numpy as np
from reefTracking.reefPixelEstimator import ReefPixelEstimator
from inference.MultiInferencer import MultiInferencer
from tools.Constants import InferenceMode

# Start Capture and Calibrate Camera
# video_path = "video/2.mkv" # or do int 0 for /dev/video0
def startDemo(videoPath=0):
    cap = cv2.VideoCapture(videoPath)  # /dev/video0
    reefEstimator = ReefPixelEstimator()
    inf = MultiInferencer(inferenceMode=InferenceMode.ONNXSMALL2025)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, reefEstimator.width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, reefEstimator.height)
    print(f"Camera Width: {reefEstimator.width} Camera Height: {reefEstimator.height}")

    def isInside(bbox, coordinate):
        p1, p2 = bbox[:2], bbox[2:]
        return np.less(p1, coordinate).all() and np.less(coordinate, p2).all()

    frame_ct = -1
    while cap.isOpened():
        ret, image = cap.read()
        frame_ct += 1

        image = cv2.undistort(image, reefEstimator.K, reefEstimator.distCoeffs)
        coordinates = reefEstimator.getReefCoordinates(image, drawCoordinates=True)
        if coordinates.items():
            results = inf.run(image, 0.8, drawBoxes=True)

            for reefId in coordinates.values():
                for offset_id, coordinate in reefId.items():
                    for result in results:
                        bbox, conf, classid = result
                        if isInside(bbox, coordinate):
                            p1 = tuple(map(int, bbox[:2]))  # Convert to integer tuple
                            p2 = tuple(map(int, bbox[2:4]))  # Convert to integer tuple
                            cv2.rectangle(image, p1, p2, (0, 255, 0), 2)

        print(f"{coordinates=}")
        cv2.imshow("frame", image)
        if cv2.waitKey(25) & 0xFF == ord("q"):
            break
