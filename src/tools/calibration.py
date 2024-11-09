import codecs
import json
import numpy as np
import cv2


def startCalibration():

    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    chessBoardDim = (7, 10)
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

            # Find the chess board corners
            ret, corners = cv2.findChessboardCorners(gray, chessBoardDim, None)

            # If found, add object points, image points (after refining them)
            if ret == True:
                objpoints.append(objp)

                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                imgpoints.append(corners2)

                # Draw and display the corners
                cv2.drawChessboardCorners(frame, chessBoardDim, corners2, ret)
            else:
                print("No corners found")

            cv2.imshow("img", frame)
            if cv2.waitKey(3000) & 0xFF == ord("q"):
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


def loadSavedCalibration():
    try:
        savedCalib = json.load(
            codecs.open("assets/camera_calib.json", "r", encoding="utf-8")
        )
        return savedCalib
    except Exception as e:
        print("Error occured when loading calibration, defaulting to saved values", e)
        return {
            "CameraMatrix": [
                [541.6373297834168, 0.0, 350.2246103229324],
                [0.0, 542.5632693416148, 224.8432462256541],
                [0.0, 0.0, 1.0],
            ],
            "DistortionCoeff": [
                [
                    0.03079145286029344,
                    -0.0037492997547329213,
                    -0.0009340163324388664,
                    0.0012027838051384778,
                    -0.07882030659375006,
                ]
            ],
        }


def createMapXYSForUndistortion(w, h):
    savedCalib = loadSavedCalibration()

    cameraMatrix = savedCalib["CameraMatrix"]
    distCoeffs = savedCalib["DistortionCoeff"]
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
    cv2.remap(frame, mapx, mapy, cv2.INTER_LINEAR)
