import codecs
import json
import os
import time
from typing import Any, Callable, Optional, Union, Tuple
import numpy as np
import cv2

# from Captures.CameraCapture import ConfigurableCameraCapture
# from abstract.Capture import ConfigurableCapture
# from tools.Constants import CameraIntrinsics

DEFAULTSAVEPATH = "assets/TMPCalibration"


def __SaveOutput(calibPath: str, mtx, dist, shape) -> None:
    if not calibPath.endswith(".json"):
        calibPath = f"{calibPath}.json"
    os.makedirs(calibPath, exist_ok=True)
    calibrationJSON = {
        "CameraMatrix": mtx.tolist(),
        "DistortionCoeff": dist.tolist(),
        "resolution": {"width": shape[1], "height": shape[0]},
    }

    json.dump(
        calibrationJSON,
        codecs.open(calibPath, "w", encoding="utf-8"),
        separators=(",", ":"),
        sort_keys=True,
        indent=4,
    )


def chessboard_calibration(
    calibPath, imagesPath=DEFAULTSAVEPATH, chessBoardDim=(7, 10)
) -> None:
    images = []
    calibshape = None
    for image_file in sorted(os.listdir(imagesPath)):
        if image_file.endswith(".jpg") or image_file.endswith(".png"):
            img = cv2.imread(os.path.join(imagesPath, image_file))
            calibshape = img.shape
            images.append(img)

    # Arrays to store object points and image points from all the images.
    objpoints = []  # 3d point in real world space
    imgpoints = []  # 2d points in image plane.

    # termination criteria
    criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.001)
    # prepare object points, like (0,0,0), (1,0,0), (2,0,0) ....,(6,5,0)
    objp = np.zeros((chessBoardDim[0] * chessBoardDim[1], 3), np.float32)
    objp[:, :2] = (
        np.mgrid[0 : chessBoardDim[0], 0 : chessBoardDim[1]].T.reshape(-1, 2) * 2
    )

    for image in images:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        # Find the chess board corners
        ret, corners = cv2.findChessboardCorners(gray, chessBoardDim, None)
        # If found, add object points, image points (after refining them)
        if ret:
            objpoints.append(objp)

            corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
            imgpoints.append(corners2)

    if imgpoints:
        print(f"Using: {len(imgpoints)} points")
        ret_val, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
            objpoints, imgpoints, gray.shape[::-1], None, None
        )
        __SaveOutput(calibPath, mtx, dist, calibshape)
        print(f"Saved calibration to {calibPath}")
    else:
        print("Failed to find chessboard points!")


def charuco_calibration(
    calibPath,
    imagesPath=DEFAULTSAVEPATH,
    arucoboarddim=(15, 15),
    runOnLoop: Optional[Callable[[np.ndarray, int], None]] = None,
):
    images = []
    calibshape = None
    for image_file in sorted(os.listdir(imagesPath)):
        if image_file.endswith((".jpg", ".png")):
            img = cv2.imread(os.path.join(imagesPath, image_file))
            # Explicitly cast to tuple of ints for mypy
            h, w = img.shape[:2]
            calibshape = (int(w), int(h))  # (width, height)
            images.append(img)

    board = cv2.aruco.CharucoBoard(
        size=arucoboarddim,
        squareLength=30,
        markerLength=22,
        dictionary=cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100),
    )
    arucoParams = cv2.aruco.DetectorParameters()
    arucoParams.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

    detector = cv2.aruco.CharucoDetector(board)
    detector.setDetectorParameters(arucoParams)
    obj_points = []
    img_points = []
    imgCount = 1

    for img in images:
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        charuco_corners, charuco_ids, _, _ = detector.detectBoard(gray)
        print(f"{charuco_corners=} {charuco_ids=}")

        if charuco_corners is not None and len(charuco_corners) > 0:
            obj_pt, img_pt = board.matchImagePoints(charuco_corners, charuco_ids)
            if len(img_pt) > 0:
                obj_points.append(obj_pt)
                img_points.append(img_pt)
                cv2.aruco.drawDetectedCornersCharuco(img, charuco_corners, charuco_ids)

        if runOnLoop is not None:
            runOnLoop(img, imgCount)
        imgCount += 1

    print(f"Found {len(obj_points)} object points and {len(img_points)} image points")

    if obj_points and img_points:
        print(f"Using {len(img_points)} valid images for calibration")
        # Make sure calibshape is a tuple of ints
        if calibshape is not None and isinstance(calibshape, tuple) and len(calibshape) == 2:
            image_size = (int(calibshape[0]), int(calibshape[1]))
            ret_val, mtx, dist, rvecs, tvecs = cv2.calibrateCameraExtended(
                obj_points, img_points, image_size, None, None
            )[:5]
        else:
            # Default size if calibshape is not valid
            ret_val, mtx, dist, rvecs, tvecs = cv2.calibrateCameraExtended(
                obj_points, img_points, (640, 480), None, None
            )[:5]

        __SaveOutput(calibPath, mtx, dist, calibshape)
        print("Calibration saved to", calibPath)
        return True
    else:
        print("Failed to find enough Charuco points")
        return False
    

def charuco_calibration_videos(
    calibPath : str,
    videoPath : Any,
    arucoboarddim=(15, 15),
):
    cap = cv2.VideoCapture(videoPath)


    board = cv2.aruco.CharucoBoard(
        size=arucoboarddim,
        squareLength=30,
        markerLength=22,
        dictionary=cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_1000),
    )
    arucoParams = cv2.aruco.DetectorParameters()
    arucoParams.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

    detector = cv2.aruco.CharucoDetector(board)
    detector.setDetectorParameters(arucoParams)
    obj_points = []
    img_points = []
    maxPoints = 200
    calibshape = None
    while cap.isOpened():
        ret, frame = cap.read()
        maxPoints-=1
        
        if not ret or maxPoints <=0:
            break
        if calibshape is None:
            # Explicitly cast to tuple of ints for mypy
            h, w = frame.shape[:2]
            calibshape = (int(w), int(h))


        print(calibshape)

        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        charuco_corners, charuco_ids, _, _ = detector.detectBoard(gray)
        # print(f"{charuco_corners=} {charuco_ids=}")

        if charuco_corners is not None and len(charuco_corners) > 0:
            obj_pt, img_pt = board.matchImagePoints(charuco_corners, charuco_ids)
            if len(img_pt) > 4  and len(obj_pt) > 4:
                obj_points.append(obj_pt)
                img_points.append(img_pt)
                cv2.aruco.drawDetectedCornersCharuco(frame, charuco_corners, charuco_ids)
        
        cv2.imshow("frame",frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break        

    print(f"Found {len(obj_points)} object points and {len(img_points)} image points")

    if obj_points and img_points:
        print(f"Using {len(img_points)} valid images for calibration")
        # Make sure calibshape is a tuple of ints
        if calibshape is not None and isinstance(calibshape, tuple) and len(calibshape) == 2:
            image_size = (int(calibshape[0]), int(calibshape[1]))
            ret_val, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
                obj_points, img_points, image_size, None, None
            )[:5]
        else:
            # Default size if calibshape is not valid
            ret_val, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
                obj_points, img_points, (640, 480), None, None
            )[:5]

        __SaveOutput(calibPath, mtx, dist, calibshape)
        print("Calibration saved to", calibPath)
        return True
    else:
        print("Failed to find enough Charuco points")
        return False


def createMapXYForUndistortionFromCalib(loadedCalibration):
    resolution = loadedCalibration["resolution"]

    cameraMatrix = np.array(loadedCalibration["CameraMatrix"])
    distCoeffs = np.array(loadedCalibration["DistortionCoeff"])
    # print(cameraMatrix)
    # Compute the optimal new camera matrix
    w = resolution["width"]
    h = resolution["height"]

    newCameraMatrix, roi = cv2.getOptimalNewCameraMatrix(
        cameraMatrix, distCoeffs, (w, h), 1, (w, h)
    )

    # Generate undistortion and rectification maps
    mapx, mapy = cv2.initUndistortRectifyMap(
        cameraMatrix, distCoeffs, None, newCameraMatrix, (w, h), cv2.CV_32FC1
    )

    return mapx, mapy


# def createMapXYForUndistortion(distCoeffs, cameraIntrinsics: CameraIntrinsics):
def createMapXYForUndistortion(distCoeffs, cameraIntrinsics):
    cameraMatrix = np.array(
        [
            [cameraIntrinsics.getFx(), 0, cameraIntrinsics.getCx()],
            [0, cameraIntrinsics.getFy(), cameraIntrinsics.getCy()],
            [0, 0, 1],
        ],
        dtype=np.float32,
    )

    # Compute the optimal new camera matrix
    newCameraMatrix, roi = cv2.getOptimalNewCameraMatrix(
        cameraMatrix,
        distCoeffs,
        (cameraIntrinsics.getHres(), cameraIntrinsics.getVres()),
        1,
        (cameraIntrinsics.getHres(), cameraIntrinsics.getVres()),
    )

    # Generate undistortion and rectification maps
    mapx, mapy = cv2.initUndistortRectifyMap(
        cameraMatrix,
        distCoeffs,
        None,
        newCameraMatrix,
        (cameraIntrinsics.getHres(), cameraIntrinsics.getVres()),
        cv2.CV_32FC1,
    )

    return mapx, mapy


def undistortFrame(frame, mapx, mapy):
    return cv2.remap(frame, mapx, mapy, cv2.INTER_LINEAR)


def takeCalibrationPhotos(
    cameraPath, photoPath=DEFAULTSAVEPATH, timePerPicture=3, frameShape=(640, 480)
) -> None:
    windowName = "Calibration View"

    timePassed = 0  # ms

    cap = cv2.VideoCapture(cameraPath)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, frameShape[0])
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, frameShape[1])

    # opencv might not be able to set the frame shape you want for various reasons
    realFrameShape = (
        cap.get(cv2.CAP_PROP_FRAME_WIDTH),
        cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
    )

    frameRate = cap.get(cv2.CAP_PROP_FPS)
    print(f"fps: {frameRate}")
    print(f"W: {realFrameShape[1]} H: {realFrameShape[1]}")

    secondPerFrame = 1 / frameRate

    frameIdx = 0
    os.makedirs(photoPath, exist_ok=True)
    while cap.isOpened():
        r, frame = cap.read()

        if r:
            # Ensure this is a float for type checking
            timePassed += float(secondPerFrame)

            if timePassed > timePerPicture:
                frameIdx += 1
                timePassed = 0
                cv2.imwrite(os.path.join(photoPath, f"Frame#{frameIdx}.jpg"), frame)
                cv2.putText(
                    frame, f"Picture Taken!", (10, 30), 0, 1, (255, 255, 255), 2
                )
            else:
                cv2.putText(
                    frame,
                    f"Time Left: {(timePerPicture-timePassed):2f}",
                    (10, 30),
                    0,
                    1,
                    (255, 255, 255),
                    2,
                )

            cv2.imshow(windowName, frame)
            if timePassed == 0:
                time.sleep(1)

            if cv2.waitKey(1) & 0xFF == ord("q"):
                break


class CustomCalibrator:
    def __init__(
        self,
        # capture: ConfigurableCameraCapture,
        photoPath=DEFAULTSAVEPATH,
        timePerPicture=3,
        targetResolution=(640, 480),
    ):
        os.makedirs(photoPath, exist_ok=True)
        self.capture = capture
        self.photoPath = photoPath
        self.timePerPicture = timePerPicture
        self.targetResolution = targetResolution
        self.fps = self.initCapture()
        self.secondPerFrame = 1 / self.fps
        self.frameIdx = 0
        self.timeSincePic = 0

    def initCapture(self):
        self.capture.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.targetResolution[0])
        self.capture.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.targetResolution[1])

        # opencv might not be able to set the frame shape you want for various reasons
        realFrameShape = (
            self.capture.cap.get(cv2.CAP_PROP_FRAME_WIDTH),
            self.capture.cap.get(cv2.CAP_PROP_FRAME_HEIGHT),
        )

        frameRate = self.capture.cap.get(cv2.CAP_PROP_FPS)
        print(f"fps: {frameRate}")
        print(f"W: {realFrameShape[1]} H: {realFrameShape[1]}")
        return frameRate

    def calibrationCycle(self):
        frame = self.capture.getColorFrame()

        self.timeSincePic += self.secondPerFrame

        if self.timeSincePic > self.timePerPicture:

            self.frameIdx += 1
            self.timeSincePic = 0
            cv2.imwrite(
                os.path.join(self.photoPath, f"Frame#{self.frameIdx}.jpg"), frame
            )
            cv2.putText(frame, f"Picture Taken!", (10, 30), 0, 1, (255, 255, 255), 2)
        else:
            cv2.putText(
                frame,
                f"Time Left: {(self.timePerPicture-self.timeSincePic):2f}",
                (10, 30),
                0,
                1,
                (255, 255, 255),
                2,
            )
        return frame
