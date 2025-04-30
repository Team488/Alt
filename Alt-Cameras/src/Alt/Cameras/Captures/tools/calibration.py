import os
import numpy as np
import cv2

from Alt.Core.Utils.files import user_tmp_dir
from Alt.Core import getChildLogger

from ...Parameters.CameraCalibration import CameraCalibration


Sentinel = getChildLogger("Calibrator")

CALIBRATIONPHOTOPATH = str(user_tmp_dir / "ALT" / "Calibration")
CALIBRATIONPHOTOFILEENDING = ".jpg"
os.makedirs(CALIBRATIONPHOTOPATH, exist_ok=True)
class Calibrator:
    def __init__(
        self,
        nFrames : int,
        targetW: int,
        targetH: int,
        isCharucoBoard: bool = True
    ): 
        self.nFrames = nFrames
        self.targetW = targetW
        self.targetH = targetH
        self.frameIdx = 0
        self.isCharucoBoard = isCharucoBoard
        Sentinel.warning("Clearing any old calibration images!")
        Calibrator.__clearCalibrationPath(CALIBRATIONPHOTOPATH)

    def savePicture(self, frame : np.ndarray):
        if self.isFinished():
            raise RuntimeError("Taking pictures already finished. Please now start the calibration")

        if frame.shape[:2][::-1] != (self.targetW, self.targetH):
            raise RuntimeError("Calibration frame dimension does not match target dimensions!")

        self.frameIdx += 1
        Calibrator.saveCalibrationPicture(frame, f"Frame#{self.frameIdx}{CALIBRATIONPHOTOFILEENDING}")

    def isFinished(self):
        return self.frameIdx >= self.nFrames
    
    def startCalibration(self) -> CameraCalibration:
        if not self.isFinished():
            raise RuntimeError("Taking pictures has not finished!")
        
        if self.isCharucoBoard:
            return Calibrator.charuco_calibration()
        else:
            return Calibrator.chessboard_calibration()
        
    
    @staticmethod
    def chessboard_calibration(
        chessBoardDim=(7, 10)
    ) -> CameraCalibration:
        images, imageWH = Calibrator.__collectImages(CALIBRATIONPHOTOPATH)
        
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
            if ret == True:
                objpoints.append(objp)
                corners2 = cv2.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
                imgpoints.append(corners2)

        if imgpoints:
            Sentinel.info(f"Using: {len(imgpoints)} points")
            ret, mtx, dist, rvecs, tvecs = cv2.calibrateCamera(
                objpoints, imgpoints, gray.shape[::-1], None, None
            )
            calibration = CameraCalibration(mtx, dist, imageWH)
            return calibration

        Sentinel.warning("Failed to find chessboard points!")
        return None

    @staticmethod
    def charuco_calibration(
        arucoboarddim=(15, 15),
        squareLengthMM = 30,
        markerLengthMM = 22,
        dictionary=cv2.aruco.getPredefinedDictionary(cv2.aruco.DICT_4X4_100),
    ) -> CameraCalibration:
        images, imageWH = Calibrator.__collectImages(CALIBRATIONPHOTOPATH)

        board = cv2.aruco.CharucoBoard(
            size=arucoboarddim,
            squareLength=squareLengthMM,
            markerLength=markerLengthMM,
            dictionary=dictionary,
        )
        arucoParams = cv2.aruco.DetectorParameters()
        arucoParams.cornerRefinementMethod = cv2.aruco.CORNER_REFINE_SUBPIX

        detector = cv2.aruco.CharucoDetector(board)
        detector.setDetectorParameters(arucoParams)
        obj_points = []
        img_points = []

        for img in images:
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            charuco_corners, charuco_ids, _, _ = detector.detectBoard(gray)

            if charuco_corners is not None and len(charuco_corners) > 0:
                obj_pt, img_pt = board.matchImagePoints(charuco_corners, charuco_ids)
                if len(img_pt) > 0:
                    obj_points.append(obj_pt)
                    img_points.append(img_pt)
                    cv2.aruco.drawDetectedCornersCharuco(img, charuco_corners, charuco_ids)

        if obj_points and img_points:
            Sentinel.info(f"Using {len(img_points)} valid images for calibration")
            ret, mtx, dist, rvecs, tvecs = cv2.calibrateCameraExtended(
                obj_points, img_points, imageWH, None, None
            )[:5]

            calibration = CameraCalibration(mtx, dist, imageWH)
            return calibration

        Sentinel.warning("Failed to find enough Charuco points")
        return None
    
    @staticmethod
    def saveCalibrationPicture(frame : np.ndarray, pictureName : str):
        cv2.imwrite(
            os.path.join(CALIBRATIONPHOTOPATH, pictureName), frame
        )
    
    @staticmethod
    def __collectImages(imagePath : str) -> tuple[list[np.ndarray], tuple[int,int]]:
        images = []
        calibshape = None
        
        # sorted not really necessary. It just helps keep calibration in order if taken with the Calibratior.savePicture()
        for image_file in sorted(os.listdir(imagePath)): 
            if image_file.endswith(CALIBRATIONPHOTOFILEENDING):
                img = cv2.imread(os.path.join(imagePath, image_file))
                images.append(img)

                imgShape = img.shape[:2][::-1]  # (width, height)
                
                if calibshape is None:
                    calibshape = imgShape 
                elif calibshape == imgShape:
                    pass
                else:
                    raise RuntimeError("Calibration photo image shapes dont match!")
                
        if not images:
            raise RuntimeError(f"CALIBRATIONPHOTOPATH: {CALIBRATIONPHOTOPATH} does not have any pictures! Did you take some pictures first!")
                
        return images, calibshape
    
    @staticmethod
    def __clearCalibrationPath(imagePath : str):
        removedCnt = 0
        for image_file in os.listdir(imagePath):
            if image_file.endswith(CALIBRATIONPHOTOFILEENDING):
                os.remove(os.path.join(imagePath, image_file))
                removedCnt+=1

        Sentinel.info(f"Cleared {removedCnt} {CALIBRATIONPHOTOFILEENDING} images from {imagePath}")
        
    
     
                    
            

            
        
