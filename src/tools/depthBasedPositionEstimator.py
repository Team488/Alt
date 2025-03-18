import logging
import math
from typing import Optional, Tuple, List, Union, Any
import cv2
import numpy as np
from mapinternals.NumberMapper import NumberMapper
from tools.Constants import CameraIntrinsics, InferenceMode, Label, ObjectReferences
from Core.ConfigOperator import staticLoad
from Core import getLogger


Sentinel = getLogger("Position_Estimator")


class DepthBasedPositionEstimator:
    def __init__(self) -> None:
        """
        Initialize the depth-based position estimator
        Loads histogram files for robot color identification
        """
        hist_result = staticLoad("histograms/blueRobotHist.npy")
        if hist_result is not None:
            self.__blueRobotHist, _ = hist_result
        else:
            self.__blueRobotHist = np.zeros((256, 256), dtype=np.float32)
            Sentinel.error("Failed to load blue robot histogram")
            
        hist_result = staticLoad("histograms/redRobotHist.npy")
        if hist_result is not None:
            self.__redRobotHist, _ = hist_result
        else:
            self.__redRobotHist = np.zeros((256, 256), dtype=np.float32)
            Sentinel.error("Failed to load red robot histogram")
            
        self.__minPerc = 0.2

    def __crop_image(
        self, image: np.ndarray, bbox: Tuple[int, int, int, int], safety_margin: float = 0
    ) -> np.ndarray:  
        """
        Crop an image based on a bounding box with optional safety margin
        
        Args:
            image: The image to crop
            bbox: The bounding box (x1, y1, x2, y2)
            safety_margin: Optional safety margin in decimal percentage (e.g., 0.05 for 5% margin)
            
        Returns:
            The cropped image
        """
        x1, y1, x2, y2 = bbox

        if safety_margin != 0:
            xMax, yMax = image.shape[1], image.shape[0]
            width = x2 - x1
            height = y2 - y1
            x1 = int(np.clip(x1 - safety_margin * width, 0, xMax))
            x2 = int(np.clip(x2 + safety_margin * width, 0, xMax))
            y1 = int(np.clip(y1 - safety_margin * height, 0, yMax))
            y2 = int(np.clip(y2 + safety_margin * height, 0, yMax))

        cropped_image = image[y1:y2, x1:x2]
        return cropped_image

    def __backprojAndThreshFrame(
        self, frame: np.ndarray, histogram: np.ndarray, isBlue: bool
    ) -> np.ndarray:
        """
        Apply back projection and thresholding to a frame using a color histogram
        
        Args:
            frame: The frame to process
            histogram: The color histogram
            isBlue: Whether the histogram is for blue (True) or red (False)
            
        Returns:
            The thresholded back projection
        """
        # OpenCV calcBackProject expects a list of arrays
        channels = [frame]
        backProj = cv2.calcBackProject(channels, [1, 2], histogram, [0, 256, 0, 256], 1)
        # cv2.imshow(f"backprojb b?:{isBlue}",backProj)
        _, thresh = cv2.threshold(backProj, 50, 255, cv2.THRESH_BINARY)
        # cv2.imshow(f"thresh b?:{isBlue}",thresh)

        return thresh

    def __getMajorityWhite(
        self, thresholded_image: np.ndarray, bbox: Tuple[int, int, int, int]
    ) -> float:
        """
        Calculate the percentage of white pixels in a thresholded image within a bounding box
        
        Args:
            thresholded_image: The thresholded image
            bbox: The bounding box (x1, y1, x2, y2)
            
        Returns:
            The percentage of white pixels (0.0 to 1.0)
        """
        # Calculate the percentage of match pixels
        bumperExtracted = self.__crop_image(thresholded_image, bbox)
        if bumperExtracted.size == 0:
            return 0.0
            
        num_match = np.count_nonzero(bumperExtracted)
        matchPercentage = num_match / bumperExtracted.size
        return matchPercentage

    """ Checks a frame for two backprojections. Either a blue or red bumper. If there is enough of either color, then its a sucess and we return the backprojected value. Else a fail"""

    def __backprojCheck(
        self, 
        frame: np.ndarray, 
        redHist: np.ndarray, 
        blueHist: np.ndarray, 
        bbox: Tuple[int, int, int, int]
    ) -> Tuple[Optional[np.ndarray], Optional[bool]]:
        """
        Check if a frame contains a blue or red robot bumper
        
        Args:
            frame: The frame to check
            redHist: The red robot histogram
            blueHist: The blue robot histogram
            bbox: The bounding box of the robot
            
        Returns:
            A tuple containing (backprojected_frame, is_blue) or (None, None) if no match
        """
        redBackproj = self.__backprojAndThreshFrame(frame, redHist, False)
        blueBackproj = self.__backprojAndThreshFrame(frame, blueHist, True)
        # cv2.imshow("Blue backproj",blueBackproj)
        redPerc = self.__getMajorityWhite(redBackproj, bbox)
        bluePerc = self.__getMajorityWhite(blueBackproj, bbox)

        if redPerc > bluePerc:
            if redPerc > self.__minPerc:
                Sentinel.debug("Red success")
                return (redBackproj, False)
            else:
                # failed minimum percentage
                Sentinel.debug(f"Red fail perc : {redPerc}")
                return (None, None)
        else:
            # blue greater
            if bluePerc > self.__minPerc:
                Sentinel.debug("Blue success")
                return (blueBackproj, True)
            else:
                Sentinel.debug(f"Blue fail perc : {bluePerc}")
                return (None, None)

    def __getCentralDepthEstimateCM(self, depthFrameMM: np.ndarray, bbox, batch=5):
        # todo find calibrated values for other cams
        centerPoint = np.divide(np.add(bbox[:2], bbox[2:]), 2)
        x, y = map(int, centerPoint)
        mx = max(0, x - batch)
        my = max(0, y - batch)
        lx = min(depthFrameMM.shape[1], y + batch)
        ly = min(depthFrameMM.shape[0], y + batch)
        return np.mean(depthFrameMM[my:ly][mx:lx]) / 10

    """ calculates angle change per pixel, and multiplies by number of pixels off you are. Dimensions either rad or deg depending on ivput fov

    """

    def __calcBearing(self, fov, res, pixelDiff):
        fovperPixel = fov / res
        return -pixelDiff * fovperPixel

    def __getRobotDepthCMCOLOR(
        self, depthFrameMM: np.ndarray, colorFrame: np.ndarray, bbox: Tuple[int, int, int, int]
    ) -> Optional[float]:
        """
        Isolates robot bumper based on color, and then gets the horizontal center of the bumper
        
        Args:
            depthFrameMM: The depth frame in millimeters
            colorFrame: The color frame
            bbox: The bounding box of the robot
            
        Returns:
            The average depth in centimeters, or None if no robot is found
        """
        # Convert to LAB color space
        labFrame = cv2.cvtColor(colorFrame, cv2.COLOR_BGR2LAB)
        processed, isBlue = self.__backprojCheck(
            labFrame, self.__redRobotHist, self.__blueRobotHist, bbox
        )
        if isBlue is None or processed is None:
            return None
            
        # Adjust kernel size and iterations based on frame size
        bumperKernel = np.ones((2, 2), np.uint8)
        iterations_close = 1
        iterations_open = 1

        # Morphological operations for bumper
        bumper_closed = cv2.morphologyEx(
            processed, cv2.MORPH_CLOSE, bumperKernel, iterations=iterations_close
        )
        bumper_opened = cv2.morphologyEx(
            bumper_closed, cv2.MORPH_OPEN, bumperKernel, iterations=iterations_open
        )

        _, thresh = cv2.threshold(bumper_opened, 50, 255, cv2.THRESH_BINARY)
        thresh_mask = thresh == 255

        depth_masked = depthFrameMM[thresh_mask]
        # mm->cm
        average_depth = np.mean(depth_masked) / 10 if depth_masked.size > 0 else None
        return average_depth

    def __getRobotDepthCM(self, depthFrameMM: np.ndarray, bbox: Tuple[int, int, int, int]) -> Optional[float]:
        """
        Isolates robot bumper based on depth discontinuities
        
        Args:
            depthFrameMM: The depth frame in millimeters
            bbox: The bounding box of the robot (x1, y1, x2, y2)
            
        Returns:
            The depth in centimeters, or None if no valid depth is found
        """
        x1, y1, x2, y2 = bbox
        midX = min(int((x1 + x2) / 2), depthFrameMM.shape[1] - 1)
        botY = y2 - 1
        step = -1

        # Calculate depth differences in vertical direction
        deltas = np.diff(depthFrameMM[:, midX])

        diffThresh = 10  # looking for less than 10 mm change in direction

        selectedDepth = None
        while botY >= 0:
            delta = deltas[botY]
            if abs(delta) < diffThresh:
                selectedDepth = depthFrameMM[botY, midX]
                # Use a sequence for the color parameter to match OpenCV's type expectations
                cv2.circle(
                    depthFrameMM,
                    center=(midX, botY),
                    radius=2,
                    color=(99999, 99999, 99999),  # Use a sequence for color
                    thickness=-1,
                )

                # add depth line here - search horizontally for similar depths
                dirs = (1, -1)
                deltasHorizontal = np.diff(depthFrameMM[botY, :])
                for dir in dirs:
                    nx = midX + dir
                    while (
                        0 <= nx < len(deltasHorizontal)
                        and abs(deltasHorizontal[nx]) < diffThresh
                    ):
                        # Use a sequence for the color parameter to match OpenCV's type expectations
                        cv2.circle(
                            depthFrameMM,
                            center=(nx, botY),
                            radius=2,
                            color=(99999, 99999, 99999),  # Use a sequence for color
                            thickness=-1,
                        )

                        depthProbe = depthFrameMM[botY, nx]

                        if selectedDepth is not None and depthProbe is not None:
                            selectedDepth = min(selectedDepth, depthProbe)
                        nx += dir

                break

            botY += step

        # Convert from mm to cm
        return selectedDepth / 10 if selectedDepth is not None else None

    def __estimateRelativeRobotPosition(
        self,
        colorFrame: np.ndarray,
        depthFrameMM: np.ndarray,
        boundingBox: Tuple[int, int, int, int],
        cameraIntrinsics: CameraIntrinsics,
    ) -> Optional[Tuple[float, float]]:
        """
        Estimate the relative position of a robot
        
        Args:
            colorFrame: The color frame
            depthFrameMM: The depth frame in millimeters
            boundingBox: The bounding box of the robot (x1, y1, x2, y2)
            cameraIntrinsics: The camera intrinsics
            
        Returns:
            A tuple containing (x, y) coordinates in centimeters, or None if no valid position is found
        """
        x1, _, x2, _ = boundingBox
        centerX = (x2 + x1) / 2
        depthCM = self.__getRobotDepthCM(depthFrameMM, boundingBox)

        if depthCM is not None and depthCM > 0 and not math.isnan(depthCM):
            bearing = self.__calcBearing(
                CameraIntrinsics.getVfov(cameraIntrinsics, radians=True),
                cameraIntrinsics.getHres(),
                int(centerX - cameraIntrinsics.getCx()),
            )
            Sentinel.debug(f"{depthCM=} {bearing=}")
            estCoords = self.componentizeMagnitudeAndBearing(depthCM, bearing)

            return estCoords

        return None

    def __simpleEstimatePosition(
        self, 
        depthFrameMM: np.ndarray, 
        boundingBox: Tuple[int, int, int, int], 
        cameraIntrinsics: CameraIntrinsics
    ) -> Optional[Tuple[float, float]]:
        """
        Estimate the position of a generic object using central depth estimate
        
        Args:
            depthFrameMM: The depth frame in millimeters
            boundingBox: The bounding box of the object (x1, y1, x2, y2)
            cameraIntrinsics: The camera intrinsics
            
        Returns:
            A tuple containing (x, y) coordinates in centimeters, or None if no valid position is found
        """
        x1, _, x2, _ = boundingBox
        centerX = (x2 + x1) / 2
        depthCM = self.__getCentralDepthEstimateCM(
            depthFrameMM,
            boundingBox,
        )

        if depthCM is not None and depthCM > 0 and not math.isnan(depthCM):
            bearing = self.__calcBearing(
                CameraIntrinsics.getVfov(cameraIntrinsics, radians=True),
                cameraIntrinsics.getHres(),
                int(centerX - cameraIntrinsics.getCx()),
            )
            Sentinel.debug(f"{depthCM=} {bearing=}")
            estCoords = self.componentizeMagnitudeAndBearing(depthCM, bearing)
            return estCoords
            
        return None

    def __estimateRelativePosition(
        self,
        class_idx: int,
        colorFrame: np.ndarray,
        depthframeMM: np.ndarray,
        bbox: Union[List[int], Tuple[int, int, int, int]],
        cameraIntrinsics: CameraIntrinsics,
        inferenceMode: InferenceMode,
    ) -> Optional[Tuple[float, float]]:
        """
        Estimate the relative position of an object based on its class index
        
        Args:
            class_idx: The class index of the object
            colorFrame: The color frame
            depthframeMM: The depth frame in millimeters
            bbox: The bounding box of the object (x1, y1, x2, y2)
            cameraIntrinsics: The camera intrinsics
            inferenceMode: The inference mode
            
        Returns:
            A tuple containing (x, y) coordinates in centimeters, or None if no valid position is found
        """
        labels = inferenceMode.getLabels()
        if class_idx < 0 or class_idx >= len(labels):
            Sentinel.warning(
                f"Estimate relative position got an out of bounds class_idx: {class_idx}"
            )
            return None

        # Convert list to tuple if needed, ensuring it has 4 elements
        if isinstance(bbox, list):
            if len(bbox) == 4:
                bbox_tuple = (bbox[0], bbox[1], bbox[2], bbox[3])
            else:
                Sentinel.warning(f"Bounding box must have 4 elements, got {len(bbox)}: {bbox}")
                return None
        else:
            bbox_tuple = bbox
        
        label = labels[class_idx]
        if label == Label.ROBOT:
            return self.__estimateRelativeRobotPosition(
                colorFrame, depthframeMM, bbox_tuple, cameraIntrinsics
            )
        if label in {Label.NOTE, Label.ALGAE, Label.CORAL}:
            return self.__simpleEstimatePosition(depthframeMM, bbox_tuple, cameraIntrinsics)
            
        Sentinel.warning(
            f"Label: {str(label)} is not supported for position estimation!"
        )
        return None

    def estimateDetectionPositions(
        self,
        colorFrame: np.ndarray,
        depthframeMM: np.ndarray,
        labledResults,
        cameraIntrinsics: CameraIntrinsics,
        inferenceMode: InferenceMode,
    ):
        if colorFrame.shape[:2] != depthframeMM.shape[:2]:
            Sentinel.fatal(
                f"colorFrame and depth frame shape must match! {colorFrame.shape=} {depthframeMM.shape=}"
            )
            raise ValueError(
                f"colorFrame and depth frame shape must match! {colorFrame.shape=} {depthframeMM.shape=}"
            )

        estimatesOut = [
            [result[0], estimate, result[2], result[3], result[4]]
            for result in labledResults
            if (
                estimate := self.__estimateRelativePosition(
                    result[3],
                    colorFrame,
                    depthframeMM,
                    result[1],
                    cameraIntrinsics,
                    inferenceMode,
                )
            )
        ]

        return estimatesOut

    """ This follows the idea that the distance we calculate is independent to bearing. This means that the distance value we get is the X dist. Thus  y will be calculated using bearing
        Takes hDist, bearing (radians) and returns x,y
    """

    def componentizeHDistAndBearing(self, hDist, bearing):
        x = hDist
        y = math.tan(bearing) * hDist
        return x, y

    def componentizeMagnitudeAndBearing(self, magnitude, bearing):
        x = math.cos(bearing) * magnitude
        y = math.sin(bearing) * magnitude
        return x, y
