import codecs
import json
import numpy as np
import cv2
from tools.configLoader import loadSavedCalibration

def startCalibration(chessBoardDim = (7, 10)):
    windowName = "Calibration View"
    cv2.namedWindow(windowName)
    trackbarName = "Time Per Cap: "

    cv2.createTrackbar(trackbarName, windowName, 3, 5, lambda x : None)

    waitTime = 3000  # default 3s per capture
    frameRate = 1  # 1ms wait
    timePassed = 0  # ms
    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((chessBoardDim[0] * chessBoardDim[1], 3), np.float32)
    objp[:, :2] = (
        np.mgrid[0 : chessBoardDim[0], 0 : chessBoardDim[1]].T.reshape(-1, 2) * 2
    )

    # Arrays to store object points and image points from all the images.
    objpoints = []  # 3d point in real world space
    imgpoints = []  # 2d points in image plane.

    cap = cv2.VideoCapture(0)

    while cap.isOpened():
        r, frame = cap.read()
        if r:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            timePassed += frameRate

            cv2.putText(
                frame, f"{timePassed/1000:.2f}", (10, 30), 0, 1, (255, 255, 255), 2
            )

            if timePassed > waitTime:
                timePassed = 0

                # Find the chess board corners
                ret, corners = cv2.findChessboardCorners(gray, chessBoardDim, None)

                # If found, add object points, image points (after refining them)
                if ret == True:
                    objpoints.append(objp)

                    corners2 = cv2.cornerSubPix(
                        gray, corners, (11, 11), (-1, -1), criteria
                    )
                    imgpoints.append(corners2)

                    # Draw and display the corners
                    cv2.drawChessboardCorners(frame, chessBoardDim, corners2, ret)
                else:
                    print("No corners found")

            cv2.imshow("img", frame)
            if cv2.waitKey(frameRate) & 0xFF == ord("q"):
                break

    print(f"Using: {len(imgpoints)} points")
    ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
        objpoints, imgpoints, gray.shape[::-1], None, None
    )

    calibrationJSON = {
        "CameraMatrix": json.dumps(mtx.tolist()),
        "DistortionCoeff": json.dumps(dist.tolist()),
    }

    json.dump(
        calibrationJSON,
        codecs.open("assets/camera_calib.json", "w", encoding="utf-8"),
        separators=(",", ":"),
        sort_keys=True,
        indent=4,
    )
    cv2.destroyAllWindows()
    cap.release()





def createMapXYForUndistortion(w, h, loadedCalibration):
    cameraMatrix = np.array(loadedCalibration["CameraMatrix"])
    distCoeffs = np.array(loadedCalibration["DistortionCoeff"])
    # print(cameraMatrix)
    # Compute the optimal new camera matrix
    newCameraMatrix, roi = cv2.getOptimalNewCameraMatrix(
        cameraMatrix, distCoeffs, (w, h), 1, (w, h)
    )

    # Generate undistortion and rectification maps
    mapx, mapy = cv2.initUndistortRectifyMap(
        cameraMatrix, distCoeffs, None, newCameraMatrix, (w, h), cv2.CV_32FC1
    )

    return mapx, mapy


def undistortFrame(frame, mapx, mapy):
    return cv2.remap(frame, mapx, mapy, cv2.INTER_LINEAR)
