import logging
import math
import cv2
import numpy as np
from mapinternals.NumberMapper import NumberMapper
from tools.Constants import CameraIntrinsics, ObjectReferences


class PositionEstimator:
    def __init__(self, tryocr=False) -> None:
        self.tryocr = tryocr
        self.numMapper = NumberMapper(["6328"],["6328"])
        if tryocr:
            import pytesseract

            pytesseract.pytesseract.tesseract_cmd = (
                r"c:/Program Files/Tesseract-OCR/tesseract.exe"
            )
            self.pytesseract = pytesseract
        self.__minPerc = 0.005  # minimum percentage of bounding box with bumper color
        self.__blueRobotHist = np.load("assets/simulationBlueRobotHist.npy")
        self.__redRobotHist = np.load("assets/redRobotHist.npy")
        self.__MAXRATIO = 4.5  # max ratio between number width/height or vice versa

    """ Extract a rectangular slice of the image, given a bounding box. This is axis aligned"""

    def __crop_image(self, image, top_left, bottom_right,safety_margin = 0): # in decimal percentage. Eg 5% margin -> 0.05
        x1, y1 = top_left
        x2, y2 = bottom_right
        if safety_margin != 0:
            xMax,yMax = image.shape[1],image.shape[0]
            x1 = int(np.clip(x1*(1+safety_margin),0,xMax))
            x2 = int(np.clip(x2*(1+safety_margin),0,xMax))
            y1 = int(np.clip(y1*(1+safety_margin),0,yMax))
            y2 = int(np.clip(y2*(1+safety_margin),0,yMax))

        cropped_image = image[y1:y2, x1:x2]

        return cropped_image

    """ Keep only inside a specified contour and make the rest black"""

    def __crop_contours(self, image, contour):
        # Unpack the rectangle properties
        mask = np.zeros_like(image)

        # Draw the convex hull on the mask
        cv2.drawContours(mask, [contour], -1, (255, 255, 255), thickness=cv2.FILLED)
        result = np.zeros_like(image)

        # Copy the region of interest using the mask
        result[mask == 255] = image[mask == 255]
        return result

    """ White color backprojection"""

    def __backProjWhite(self, labImage, threshold=120):
        # return cv2.calcBackProject([bumperOnlyLab],[1,2],whiteNumHist,[0,256,0,256],1)
        L, a, b = cv2.split(labImage)

        # Threshold the L channel to get a binary image
        # Here we assume white has high L values, you might need to adjust the threshold value
        _, white_mask = cv2.threshold(L, threshold, 255, cv2.THRESH_BINARY)

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

    """ Checks a frame for two backprojections. Either a blue or red bumper. If there is enough of either color, then its a sucess and we return the backprojected value. Else a fail"""

    def __backprojCheck(self, frame, redHist, blueHist):
        redBackproj = self.__backprojAndThreshFrame(frame, redHist, False)
        blueBackproj = self.__backprojAndThreshFrame(frame, blueHist, True)
        # cv2.imshow("Blue backproj",blueBackproj)
        redPerc = self.__getMajorityWhite(redBackproj)
        bluePerc = self.__getMajorityWhite(blueBackproj)

        if redPerc > bluePerc:
            if redPerc > self.__minPerc:
                print("Red suceess")
                return (redBackproj, False)
            else:
                # failed minimum percentage
                print("Red fail", redPerc)
                return (None, None)
        else:
            # blue greater
            if bluePerc > self.__minPerc:
                print("blue sucess")
                return (blueBackproj, True)
            else:
                print("blue fail", bluePerc)
                return (None, None)

    """ Calculates distance from object assuming we know real size and pixel size. Dimensions out are whatever known size dimensions are
        Its as follows
        knownSize(whatever length dim) * focallength(px)/currentsizePixels(px))

        Output dim is whatever length dim
    """

    def __calculateDistance(self, knownSize, currentSizePixels, focalLengthPixels):
        # todo find calibrated values for other cams
        return (knownSize * focalLengthPixels) / (currentSizePixels)

    """ calculates angle change per pixel, and multiplies by number of pixels off you are. Dimensions are whatever fov per pixel dimensions are

    """

    def __calcBearing(self, fov, res, pixelDiff):
        fovperPixel = fov / res
        return -pixelDiff * fovperPixel

    """
        This is a multistep process to estimate the height of a robot bumper. TLDR use number on the side of bumper to estimate height

        A couple of assumptions at play here, but they seem to always be the case
        Assuming that the number on the side of the bumper is the same height as the bumper
        Assuming that there is a number on every side of the bumper
        Assuming that the detection bounding box ecompasses the whole robot, and thus the bumper will be in the lower half of the clipped bounding box provided

        Steps
        #1 Isolate bottom half of cropped out robot detection.
        #2 try to backproject a red or blue histogram to isolate the bumper. NOTE: it is critical that histograms be updated in every different lighting condiditon (Todo make a better histogram tool)
        #3 if you pass and there is significant red or blue in the frame to indicate a bumper, now we "cut out" the bumper which is found using contours and convex hull.
        #4 we threshold for a white value because the numbers are white. (Possible todo: Use histograms instead)
        #5 we try to isolate numbers from the thresholded white value. We check to see if any "numbers" found are actually number shaped with some simple ratio checks
        #6 if we have found a proper number, we get its height and take that as the bumper height

    """

    def __estimateRobotBumperHeight(self, croppedframe) -> tuple[float, bool]:
        y = croppedframe.shape[0]
        x = croppedframe.shape[1]
        # cutting the frame as for all the images i have the bumper is always in the bottom half
        croppedframe = self.__crop_image(croppedframe, (0, int(y / 2)), (x, y))
        # cv2.imshow("Cropped frame",croppedframe)
        labFrame = cv2.cvtColor(croppedframe, cv2.COLOR_BGR2LAB)
        processed, isBlue = self.__backprojCheck(
            labFrame, self.__redRobotHist, self.__blueRobotHist
        )
        if isBlue != None:
            cv2.imshow("processed",processed)
            # a bumper with enough percentage was detected
            bumperKernel = np.ones((2, 2), np.uint8)
            bumper_closed = cv2.morphologyEx(processed, cv2.MORPH_CLOSE, bumperKernel, iterations=2)
            cv2.imshow("close bumper",bumper_closed)
            bumper_opened = cv2.morphologyEx(bumper_closed,cv2.MORPH_OPEN,bumperKernel,iterations=2)
            cv2.imshow("open bumper",bumper_opened)

            # morphology_final = cv2.morphologyEx(thresh, cv2.MORPH_RECT, kernel, None, (-1, -1), 4)
            contours, _ = cv2.findContours(
                bumper_opened, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
            )
            contour_image = np.zeros_like(bumper_opened)
            cv2.drawContours(contour_image,contours,-1,(255),1)
            cv2.imshow("Countour image",contour_image)
            if contours:
                # extracting the bumper
                combined_contour = np.concatenate(contours)
                convex_hull = cv2.convexHull(combined_contour)
                # Get bumper estimated width and height
                # cropping out only the bumper
                bumperOnlyLab = self.__crop_contours(labFrame, convex_hull)
                bumperOnly = self.__crop_contours(croppedframe, convex_hull)
                # pulling out the numbers
                kerneltwobytwo = np.ones((2, 2), np.uint8)
                kernelthreebythree = np.ones((3, 3), np.uint8)
                backProjNumbers = self.__backProjWhite(bumperOnlyLab)
                # partial cleanup #1 (this is so we keep try to do ocr before removing any sign of numbers with out next close op)
                initalOpen = cv2.morphologyEx(backProjNumbers, cv2.MORPH_OPEN, kerneltwobytwo, iterations=1)
                cv2.imshow("initialOpen",initalOpen)
                nums = ""
                if self.tryocr:
                    nums = self.pytesseract.image_to_string(backProjNumbers)
                    # cv2.putText(backProjNumbers,nums,(10,25),0,1,(255,255,255),2)
                # now merge any numbers into one
                close = cv2.morphologyEx(initalOpen, cv2.MORPH_CLOSE, kerneltwobytwo, iterations=1)
                cv2.imshow("initialClose",close)
                # one last opening to remove any noise on the edges of the numbers we extract
                final_open = cv2.morphologyEx(close,cv2.MORPH_OPEN,kerneltwobytwo,iterations=1)
                cv2.imshow("finalOpen",final_open)
                # some cleanup dilation (small amount)
                final_number_image = cv2.morphologyEx(final_open,cv2.MORPH_DILATE,kerneltwobytwo,iterations=3)
                
                _, threshNumbers = cv2.threshold(final_number_image, 50, 255, cv2.THRESH_BINARY)
                contoursNumbers, _ = cv2.findContours(
                    threshNumbers, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
                )
                cv2.imshow("Unprocessed Number image",backProjNumbers)
                cv2.imshow("Final morphed Number image",final_number_image)
                cv2.imshow("Bumper image",bumperOnly)
                # try to isolate bumper digits for their height
                if contoursNumbers:
                    # largestAcceptable_contour = np.concatenate(contoursNumbers)
                    largestAcceptable_contour = None
                    largest_size = -1
                    for contour in contoursNumbers:
                        #     # try to find digits
                        min_area_rect = cv2.minAreaRect(contour)
                        # Get the minimum area rectangle
                        # Get width and height
                        (numberWidth, numberHeight) = min_area_rect[1]
                        if numberHeight == 0 or numberWidth == 0:
                            continue
                        ratio = max(numberWidth, numberHeight) / min(
                            numberWidth, numberHeight
                        )
                        print("Ratio", ratio)
                        # Calculate the max of width and height
                        size_Score = numberWidth*numberHeight

                        if ratio < 13 and size_Score > largest_size:
                            largest_size = size_Score
                            largestAcceptable_contour = contour

                    if largestAcceptable_contour is not None:
                        epsilon = cv2.getTrackbarPos("Epsillon","Simulation Window")/1000 * cv2.arcLength(largestAcceptable_contour, True)  # Adjust epsilon for accuracy
                        approx = cv2.approxPolyDP(largestAcceptable_contour, epsilon, True)
                        approximage = np.zeros_like(close)

                        # Check if the approximated contour is a rectangle
                            # Draw the rectangle on the original image (for visualization)
                        cv2.drawContours(approximage, [approx], -1, (255, 255, 255), 2)
                        cv2.imshow("poly dp number approx", approximage)
                        
                        
                        contourimage = np.zeros_like(close)
                        cv2.drawContours(
                            contourimage, [largestAcceptable_contour], 0, (255, 255, 0), -1
                        )
                        # last cleanup of edges
                        # cv2.imshow("Best contour",frame)
                        min_area_rect = cv2.minAreaRect(largestAcceptable_contour)
                        box = cv2.boxPoints(min_area_rect)
                        box = np.int0(box)
                        cv2.drawContours(contourimage,[box],0,(255),2)

                        # Get width and height
                        (numberWidth, numberHeight) = min_area_rect[1]
                        # print(f"{numberWidth=}  {numberHeight=} ")
                        targetheight = min(numberHeight, numberWidth)
                        heightframe = np.zeros((200,400),dtype=np.uint8)
                        # cv2.putText(heightframe,f"H:{targetheight:.5f} Num:{self.numMapper.getRobotNumberEstimate(isBlue,nums)}",(10,30),0,1,(255),2)
                        cv2.imshow("Height estimate",heightframe)
                        print(f"HEIGHT----------------------------{targetheight}----------------------------")
                        cv2.imshow("Number Contour image",contourimage)
                        # cv2.drawContours(bumperOnly,[largestAcceptable_contour],0,[0,0,255],2)
                        return (targetheight, isBlue, nums)
                        
                else:
                    logging.warning("Failed to extract number from countour!")
            else:
                logging.warning("Failed to extract a bumper, not enough contour area!")
        return None

    """ Method takes in a frame, where you have already run your model. It crops out bounding boxes for each robot detection and runs a height estimation.
        If it does not fail, it then takes that information, along with a calculated bearing to estimate a relative position
       """

    def __estimateRelativeRobotPosition(
        self, frame, boundingBox, cameraIntrinsics: CameraIntrinsics
    ) -> tuple[float, float]:
        x1, y1, x2, y2 = boundingBox
        w = x2 - x1
        h = y2 - y1
        midW = int(w / 2)
        midH = int(h / 2)
        centerX = x1 + midW
        croppedImg = self.__crop_image(frame, (x1, y1), (x2, y2),safety_margin=0.07)
        est = self.__estimateRobotBumperHeight(croppedImg)
        if est is not None:
            (estimatedHeight, isBlue, nums) = est
            distance = self.__calculateDistance(
                ObjectReferences.BUMPERHEIGHT.getMeasurementCm(),
                estimatedHeight,
                cameraIntrinsics.getFy(),
            )* (cv2.getTrackbarPos("Scale Factor", "Simulation Window")/100)
            print(f"{distance=} {est=}")
            bearing = self.__calcBearing(
            cameraIntrinsics.getHFov(),
            cameraIntrinsics.getHres(),
            int(centerX - cameraIntrinsics.getCx()),
            )
            estCoords = self.componentizeHDistAndBearing(distance, bearing)

            return estCoords

        return None

    """ This current method estimates the position of a note, by using the same method as a robot. However it is slightly simplified, as we can take avantage of the circular nature of a note
        By taking the width of a note (or the max of w and h to cover the case when its vertical), we can find a pretty much exact value for the size of the note in pixels. Given we know the
        exact size of a note, we can then use this to estimate distance.

    """

    def __estimateRelativeGameObjectPosition(
        self, frame, boundingBox, cameraIntrinsics: CameraIntrinsics
    ) -> tuple[float, float]:
        x1, y1, x2, y2 = boundingBox
        w = x2 - x1
        h = y2 - y1
        midW = int(w / 2)
        # midH = int(h / 2)
        centerX = x1 + midW
        objectSize = max(w, h)
        distance = self.__calculateDistance(
            ObjectReferences.NOTE.getMeasurementCm(),
            objectSize,
            cameraIntrinsics.getFx(),
        )
        bearing = self.__calcBearing(
            cameraIntrinsics.getHFov(),
            cameraIntrinsics.getHres(),
            int(centerX - cameraIntrinsics.getCx()),
        )
        estCoords = self.componentizeHDistAndBearing(distance, bearing)
        return estCoords

    def estimateDetectionPositions(
        self, frame, labledResults, cameraIntrinsics: CameraIntrinsics
    ):
        estimatesOut = []

        # id 0 == robot 1 == note
        for result in labledResults:
            isRobot = result[3]
            bbox = result[1]
            estimate = None
            if isRobot:
                estimate = self.__estimateRelativeRobotPosition(
                    frame, bbox, cameraIntrinsics
                )

            else:
                estimate = self.__estimateRelativeGameObjectPosition(
                    frame, bbox, cameraIntrinsics
                )
            if estimate is not None:
                estimatesOut.append(
                    [result[0], estimate, result[2], isRobot, result[4]]
                )  # replace local bbox with estimated position
            # else we dont include this result
            # todo keep a metric of failed estimations
            else:
                print("Failed estimation")

        return estimatesOut

    """ This follows the idea that the distance we calculate is independent to bearing. This means that the distance value we get is the X dist. Thus  y will be calculated using bearing
        Takes hDist, bearing (radians) and returns x,y
    """

    def componentizeHDistAndBearing(self, hDist, bearing):
        x = hDist
        y = math.tan(bearing) * hDist
        return x, y
