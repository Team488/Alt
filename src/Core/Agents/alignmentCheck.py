import cv2
import numpy as np
from Core.Agents.Abstract import CameraUsingAgentBase
from Captures.FileCapture import FileCapture

from functools import partial
from abstract.Agent import Agent

from abstract.Agent import Agent


class AlignmentChecker(CameraUsingAgentBase):
    DEFAULTTHRESH = 10

    def __init__(self, showFrames: bool):
        mjpeg_url = "http://photonvisionfrontleft.local:1181/stream.mjpg"
        super().__init__(
            capture=FileCapture(videoFilePath=mjpeg_url), showFrames=showFrames
        )

    def create(self) -> None:
        super().create()
        self.offAngleProp = self.propertyOperator.createCustomReadOnlyProperty(
            propertyTable="ALIGNOFF",
            propertyValue=-1,
            addBasePrefix=True,
            addOperatorPrefix=False,
        )
        self.cameraIntrinsics = self.propertyOperator.createProperty(
            propertyTable="photonvision.Apriltag_FrontRight_Camera.cameraIntrinsics",
            propertyDefault=None,
            addBasePrefix=False,
            addOperatorPrefix=False,
            setDefaultOnNetwork=False,
            isCustom=True,
        )
        self.threshold_pixels = self.propertyOperator.createProperty(
            propertyTable="threshold_pixels",
            propertyDefault=self.DEFAULTTHRESH,
            setDefaultOnNetwork=True,
        )

    def runPeriodic(self) -> None:
        super().runPeriodic()
        frame = self.latestFrameCOLOR
        # 1. Convert to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # 2. Threshold the image
        _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

        # 3. Find contours
        contours, _ = cv2.findContours(
            thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Prepare an empty image (same size as frame) to visualize contours
        contour_img = np.zeros_like(frame)

        if contours:
            # Pick the largest contour (assuming that's the main black rectangle)
            largest_contour = max(contours, key=cv2.contourArea)

            # Compute bounding box (x, y, w, h)
            x, y, w, h = cv2.boundingRect(largest_contour)

            # Calculate left and right offsets
            left_offset = x
            right_offset = frame.shape[1] - (x + w)
            print(
                f"Left offset: {left_offset:.1f}px, Right offset: {right_offset:.1f}px"
            )

            # 4. Check if it's horizontally centered
            image_center_x = frame.shape[1] / 2
            box_center_x = x + w / 2
            horizontal_offset = abs(image_center_x - box_center_x)
            self.offAngleProp.set(horizontal_offset)

            # Print whether it's centered within 'threshold_pixels'
            if horizontal_offset <= self.threshold_pixels.get():
                print(
                    f"Box is centered (horizontal offset = {horizontal_offset:.1f}px)."
                )
            else:
                print(
                    f"Box is NOT centered (horizontal offset = {horizontal_offset:.1f}px)."
                )

            # Draw bounding box on the main frame
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Draw all contours in a separate image
            cv2.drawContours(contour_img, contours, -1, (0, 0, 255), 2)
            # And draw the bounding box there as well
            cv2.rectangle(contour_img, (x, y), (x + w, y + h), (0, 255, 0), 2)

    def getName(self) -> str:
        return "AprilTagReefAlignmentCheck"

    def getDescription(self) -> str:
        return "Looks-At-Camera-April-Tag-Checks-Alignment"


def partialAlignmentCheck(showFrames: bool = False):
    return partial(AlignmentChecker, showFrames=showFrames)
