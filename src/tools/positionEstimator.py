import math
import cv2
import numpy as np
from tools.Constants import CameraIntrinsics, ObjectReferences


class PositionEstimator:
    def __init__(self) -> None:
        self.__RobotId = 0  # yolo returned ids
        self.__minPerc = 0.05  # minimum percentage of bounding box with bumper color
        self.__blueRobotHist = np.load("assets/blueRobotHist.npy")
        self.__redRobotHist = np.load("assets/redRobotHist.npy")
        self.__MAXRATIO = 3.7  # max ratio between number width/height or vice versa

    def __crop_image(self, image, top_left, bottom_right):
        x1, y1 = top_left
        x2, y2 = bottom_right

        cropped_image = image[y1:y2, x1:x2]

        return cropped_image

    def __crop_contours(self, image, combinedContour):
        # Unpack the rectangle properties
        mask = np.zeros_like(image)

        # Draw the convex hull on the mask
        cv2.drawContours(
            mask, [combinedContour], -1, (255, 255, 255), thickness=cv2.FILLED
        )
        result = np.zeros_like(image)

        # Copy the region of interest using the mask
        result[mask == 255] = image[mask == 255]
        return result

    def __backProjWhite(self, labImage):
        # return cv2.calcBackProject([bumperOnlyLab],[1,2],whiteNumHist,[0,256,0,256],1)
        L, a, b = cv2.split(labImage)

        # Threshold the L channel to get a binary image
        # Here we assume white has high L values, you might need to adjust the threshold value
        _, white_mask = cv2.threshold(L, 175, 255, cv2.THRESH_BINARY)

        # kernel = np.ones((5, 5), np.uint8)
        # white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_OPEN, kernel)
        # white_mask = cv2.morphologyEx(white_mask, cv2.MORPH_CLOSE, kernel)
        return white_mask

    # returns the backprojected frame with either true for blue for false for red
    # if there was no color at all the frame returned will have a corresponding None value
    def __backprojAndThreshFrame(self, frame, histogram, isBlue):
        backProj = cv2.calcBackProject([frame], [1, 2], histogram, [0, 256, 0, 256], 1)
        # cv2.imshow(f"backprojb b?:{isBlue}",backProj)
        _, thresh = cv2.threshold(backProj, 50, 255, cv2.THRESH_BINARY)
        # cv2.imshow(f"thresh b?:{isBlue}",thresh)

        return thresh

    def __getMajorityWhite(self, thresholded_image):
        # Count the number of white pixels (255)
        num_white_pixels = np.sum(thresholded_image == 255)

        # Calculate the total number of pixels
        total_pixels = thresholded_image.size

        # Calculate the percentage of white pixels
        white_percentage = num_white_pixels / total_pixels
        return white_percentage

    def __backprojCheck(self, frame, redHist, blueHist):
        redBackproj = self.__backprojAndThreshFrame(frame, redHist, False)
        blueBackproj = self.__backprojAndThreshFrame(frame, blueHist, True)
        redPerc = self.__getMajorityWhite(redBackproj)
        bluePerc = self.__getMajorityWhite(blueBackproj)

        if redPerc > bluePerc:
            if redPerc > self.__minPerc:
                print("Red suceess")
                return (redBackproj, False)
            else:
                # failed minimum percentage
                print("Red fail")
                return (None, None)
        else:
            # blue greater
            if bluePerc > self.__minPerc:
                print("blue sucess")
                return (blueBackproj, True)
            else:
                print("blue fail")
                return (None, None)

    def __calculateDistance(
        self, knownSize, currentSizePixels, cameraIntrinsics: CameraIntrinsics
    ):
        return (knownSize * cameraIntrinsics.getFocalLength()) / (
            cameraIntrinsics.getPixelSize() * currentSizePixels
        )

    # calculates angle change per pixel, and multiplies by number of pixels off you are
    def __calcBearing(self, fov, res, pixelDiff):
        fovperPixel = fov / res
        return -pixelDiff * fovperPixel

    def __estimateRobotHeight(self, croppedframe) -> tuple[float, bool]:
        y = croppedframe.shape[0]
        x = croppedframe.shape[1]
        # cutting the frame as for all the images i have the bumper is always in the bottom half
        croppedframe = self.__crop_image(croppedframe, (0, int(y / 2)), (x, y))
        labFrame = cv2.cvtColor(croppedframe, cv2.COLOR_BGR2LAB)
        processed, isBlue = self.__backprojCheck(
            labFrame, self.__redRobotHist, self.__blueRobotHist
        )
        if isBlue != None:
            # a bumper with enough percentage was detected
            kernel = np.ones((5, 5), np.uint8)
            dilate = cv2.morphologyEx(processed, cv2.MORPH_DILATE, kernel, iterations=1)
            # morphology_final = cv2.morphologyEx(thresh, cv2.MORPH_RECT, kernel, None, (-1, -1), 4)
            contours, _ = cv2.findContours(
                dilate, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
            )
            # Create a mask with only the largest contour filled in
            thresholdArea = 0.01
            thesholdPix = int(x * y * thresholdArea * 0.5)
            filtered_contours = [
                contour
                for contour in contours
                if cv2.contourArea(contour) >= thesholdPix
            ]
            if filtered_contours:
                # extracting the bumper
                combined_contour = np.concatenate(filtered_contours)
                convex_hull = cv2.convexHull(combined_contour)
                bumperEstRect = cv2.minAreaRect(combined_contour)
                # Get bumper estimated width and height
                (width, height) = bumperEstRect[1]
                # cropping out only the bumper
                bumperOnlyLab = self.__crop_contours(labFrame, convex_hull)
                bumperOnly = self.__crop_contours(croppedframe, convex_hull)
                # pulling out the numbers
                kernel = np.ones((5, 5), np.uint8)
                backProjNumbers = self.__backProjWhite(bumperOnlyLab)
                # opened = cv2.morphologyEx(backProjNumbers,cv2.MORPH_OPEN,kernel,iterations=1)
                # closed = cv2.morphologyEx(opened,cv2.MORPH_CLOSE,kernel,iterations=1)
                _, threshNumbers = cv2.threshold(
                    backProjNumbers, 35, 255, cv2.THRESH_BINARY
                )
                contoursNumbers, _ = cv2.findContours(
                    threshNumbers, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
                )
                # try to isolate bumper digits for their height
                if contoursNumbers:
                    largestAcceptable_contour = None
                    largest_size = 0
                    for contour in contoursNumbers:
                        #     # try to find digits
                        min_area_rect = cv2.minAreaRect(contour)
                        # Get the minimum area rectangle
                        # Get width and height
                        (bumperWidth, bumperHeight) = min_area_rect[1]
                        if bumperHeight == 0 or bumperWidth == 0:
                            continue
                        ratio = max(bumperWidth, bumperHeight) / min(
                            bumperWidth, bumperHeight
                        )
                        print("Ratio", ratio)
                        # Calculate the max of width and height
                        length = bumperWidth + bumperHeight

                        if ratio < self.__MAXRATIO and length > largest_size:
                            largest_size = length
                            largestAcceptable_contour = contour

                    if largestAcceptable_contour is not None:
                        min_area_rect = cv2.minAreaRect(largestAcceptable_contour)
                        # Get width and height
                        (numberWidth, numberHeight) = min_area_rect[1]

                        # cv2.drawContours(bumperOnly,[largestAcceptable_contour],0,[0,0,255],2)
                        convex_hull_nums = cv2.convexHull(largestAcceptable_contour)
                        minAreaNums = cv2.minAreaRect(convex_hull_nums)
                        width, height = minAreaNums[1]
                        numToBumpRatio = max(height, numberHeight) / min(
                            height, numberHeight
                        )
                        if numToBumpRatio < 3:
                            return (height, isBlue)
                        else:
                            print("Ratio to large to be acceptable", numToBumpRatio)
        return None

    def __estimateRelativeRobotPosition(
        self, frame, boundingBox, cameraIntrinsics: CameraIntrinsics
    ) -> tuple[float, float, bool]:
        x, y, w, h = boundingBox
        midW = int(w / 2)
        midH = int(h / 2)
        topX = int(x - midW)
        topY = int(y - midH)
        botX = int(x + midW)
        botY = int(y + midH)
        croppedImg = self.__crop_image(frame, (topX, topY), (botX, botY))
        est = self.__estimateRobotHeight(croppedImg)
        if est is not None:
            (estimatedHeight, isBlue) = est
            distance = self.__calculateDistance(
                ObjectReferences.BUMPERHEIGHT.getMeasurement(),
                estimatedHeight,
                cameraIntrinsics,
            )
            bearing = self.__calcBearing(
                cameraIntrinsics.getHFov(),
                cameraIntrinsics.getHres(),
                int(x - cameraIntrinsics.getHres() / 2),
            )
            estX = math.cos(bearing) * distance
            estY = math.sin(bearing) * distance
            return (estX, estY, isBlue)

        return None

    def __estimateRelativeGameObjectPosition(
        self, frame, boundingBox, cameraIntrinsics: CameraIntrinsics
    ) -> tuple[float, float]:
        x, y, w, h = boundingBox
        distance = self.__calculateDistance(
            ObjectReferences.NOTE.getMeasurement(), w, cameraIntrinsics
        )
        bearing = self.__calcBearing(
            cameraIntrinsics.getHFov(),
            cameraIntrinsics.getHres(),
            int(x - cameraIntrinsics.getHres() / 2),
        )
        estX = math.cos(bearing) * distance
        estY = math.sin(bearing) * distance
        return (estX, estY)

    def estimateDetectionPositions(
        self, frame, yoloResults, cameraIntrinsics: CameraIntrinsics
    ):
        robotEstimatesOut = []
        gameObjectEstimatesOut = []

        boxes = yoloResults[0].boxes.xywh.cpu()
        confs = yoloResults[0].boxes.conf.cpu()
        ids = yoloResults[0].boxes.cls.cpu()
        # id 0 == robot 1 == note
        for box, conf, id in zip(boxes, confs, ids):
            if id == self.__RobotId:
                robotEst = self.__estimateRelativeRobotPosition(
                    frame, box, cameraIntrinsics
                )
                if robotEst is not None:
                    robotEstimatesOut.append((robotEst, conf))
            else:
                gameObjEst = self.__estimateRelativeGameObjectPosition(
                    frame, box, cameraIntrinsics
                )
                if gameObjEst is not None:
                    gameObjectEstimatesOut.append((gameObjEst, conf))

        return (gameObjectEstimatesOut, robotEstimatesOut)
