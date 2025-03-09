from collections import defaultdict
import cv2
import numpy as np
from Core.Agents.Abstract import CameraUsingAgentBase
from Captures.FileCapture import FileCapture

from functools import partial


class BinnedVerticalAlignmentChecker(CameraUsingAgentBase):
    DEFAULTTHRESH = 10  # Default threshold in pixels

    def __init__(self, showFrames: bool, flushTimeMS: int = -1):
        mjpeg_url = "http://localhost:1181/stream.mjpg"
        super().__init__(
            capture=FileCapture(videoFilePath=mjpeg_url, flushTimeMS=flushTimeMS),
            showFrames=showFrames,
        )

    def create(self) -> None:
        super().create()
        self.leftDistanceProp = self.propertyOperator.createCustomReadOnlyProperty(
            propertyTable="verticalEdgeLeftDistancePx",
            propertyValue=-1,
            addBasePrefix=True,
            addOperatorPrefix=False,
        )
        self.rightDistanceProp = self.propertyOperator.createCustomReadOnlyProperty(
            propertyTable="verticalEdgeRightDistancePx",
            propertyValue=-1,
            addBasePrefix=True,
            addOperatorPrefix=False,
        )
        self.isCenteredConfidently = self.propertyOperator.createCustomReadOnlyProperty(
            propertyTable="verticalAlignedConfidently",
            propertyValue=False,
            addBasePrefix=True,
            addOperatorPrefix=False,
        )

        self.sobel_threshold = self.propertyOperator.createProperty(
            propertyTable="inital_sobel_thresh",
            propertyDefault=80,
            setDefaultOnNetwork=True,
        )
        self.threshold_pixels = self.propertyOperator.createProperty(
            propertyTable="vertical_threshold_pixels",
            propertyDefault=self.DEFAULTTHRESH,
            setDefaultOnNetwork=True,
        )
        self.threshold_diff_pixels = self.propertyOperator.createProperty(
            propertyTable="aligment_threshold_pixels",
            propertyDefault=self.DEFAULTTHRESH,
            setDefaultOnNetwork=True,
        )
        self.bin_size_pixels = self.propertyOperator.createProperty(
            propertyTable="binning_size_pixels",
            propertyDefault=5,
            setDefaultOnNetwork=True,
        )
        self.min_edge_height = self.propertyOperator.createProperty(
            propertyTable="min_vertical_edge_height",
            propertyDefault=250,  # Minimum height in pixels for a valid edge
            setDefaultOnNetwork=True,
        )

    def runPeriodic(self) -> None:
        super().runPeriodic()

        frame = self.latestFrameCOLOR

        # Convert to grayscale for edge detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        if self.sobel_threshold.get() > 0:
            # this threshold can be though of as a way to only get the april tag lines by first dropping anything other than a dark april tag
            _, blurred = cv2.threshold(
                blurred, self.sobel_threshold.get(), 255, cv2.THRESH_BINARY
            )

        # Use Sobel operator to detect vertical edges (x-direction)
        sobelx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        abs_sobelx = np.absolute(sobelx)
        sobel_8u = np.uint8(abs_sobelx / abs_sobelx.max() * 255)

        # Threshold the edge image
        _, thresh = cv2.threshold(sobel_8u, 100, 255, cv2.THRESH_BINARY)
        cv2.imshow("thresh", thresh)

        # Apply morphological operations to enhance vertical edges
        kernel_vertical = np.ones((5, 1), np.uint8)
        vertical_edges = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_vertical)

        # Find contours in the vertical edge image
        contours, _ = cv2.findContours(
            vertical_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        # Prepare a visualization image
        edge_viz = np.zeros_like(frame)

        min_height = self.min_edge_height.get()
        binSize = self.bin_size_pixels.get()

        valid_binned = defaultdict(list)

        # match up binned pairs

        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Filter for vertical edges (height > width and minimum height)
            if h > w and h >= min_height:
                bin_idx = h // binSize
                valid_binned[bin_idx].append(contour)

                cv2.rectangle(edge_viz, (x, y), (x + w, y + h), (0, 255, 0), 2)

        # print([(key, len(item)) for key, item in valid_binned.items()])

        # match similar heights
        bestmatch = None
        bestsize = -1
        bestPairLength = -1
        for valid_key, valid_bin in valid_binned.items():
            size = valid_key * binSize
            pairLength = min(len(valid_bin), 2)
            if pairLength >= bestPairLength:  # prioritize pair then size
                bestmatch = valid_bin[:2]  # ugly, but get only two
                bestPairLength = pairLength
            elif pairLength == bestPairLength:
                if size >= bestsize:
                    bestmatch = valid_bin[:2]

        leftDistance = -1
        rightDistance = -1

        if bestmatch is not None:
            for biggest in bestmatch:
                x, y, w, h = cv2.boundingRect(biggest)

                # draw valid vertical edge in the visualization
                cv2.drawContours(edge_viz, [biggest], -1, (0, 0, 255), 2)

                mid = x + w / 2

                isLeftEdge = mid < frame.shape[1] / 2

                distMid = int(abs(mid - frame.shape[1] / 2))

                if isLeftEdge:
                    leftDistance = distMid
                else:
                    rightDistance = distMid

                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Update properties
            self.leftDistanceProp.set(leftDistance)
            self.rightDistanceProp.set(rightDistance)

            cv2.putText(
                frame,
                f"L: {leftDistance}px, R: {rightDistance}px",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (0, 255, 0),
                2,
            )

            # Check if it's centered (distance from middle of the frame should be similar for both edges)
            if (
                leftDistance != -1
                and rightDistance != -1
                and abs(leftDistance - rightDistance) <= self.threshold_pixels.get()
            ):
                self.isCenteredConfidently.set(True)
            else:
                self.isCenteredConfidently.set(False)
        else:
            self.isCenteredConfidently.set(False)
            self.leftDistanceProp.set(-1)
            self.rightDistanceProp.set(-1)

        # If showing frames is enabled, display the edge visualization
        if self.showFrames:
            cv2.imshow("Vertical Edges", edge_viz)

    def getName(self) -> str:
        return "VerticalEdgeAlignmentCheck"

    def getDescription(self) -> str:
        return "Detects-Vertical-Edges-For-AprilTag-Alignment"


def partialVerticalAlignmentCheck(showFrames: bool = False, flushTimeMS: int = -1):
    return partial(
        BinnedVerticalAlignmentChecker, showFrames=showFrames, flushTimeMS=flushTimeMS
    )
