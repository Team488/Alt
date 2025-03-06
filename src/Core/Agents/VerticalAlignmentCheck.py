import math

import cv2
import numpy as np
from Core.Agents.Abstract import CameraUsingAgentBase
from Captures.FileCapture import FileCapture

from functools import partial
from abstract.Agent import Agent


class VerticalAlignmentChecker(CameraUsingAgentBase):
    DEFAULTTHRESH = 20  # Default threshold in pixels
    
    def __init__(self, showFrames: bool):
        mjpeg_url = "http://localhost:1181/stream.mjpg"
        super().__init__(
            capture=FileCapture(videoFilePath=mjpeg_url), showFrames=showFrames
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
        self.threshold_pixels = self.propertyOperator.createProperty(
            propertyTable="vertical_threshold_pixels",
            propertyDefault=self.DEFAULTTHRESH,
            setDefaultOnNetwork=True,
        )
        self.min_edge_height = self.propertyOperator.createProperty(
            propertyTable="min_vertical_edge_height",
            propertyDefault=50,  # Minimum height in pixels for a valid edge
            setDefaultOnNetwork=True,
        )
        
    def runPeriodic(self) -> None:
        super().runPeriodic()
        
        frame = self.latestFrameCOLOR
        
        # Convert to grayscale for edge detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Use Sobel operator to detect vertical edges (x-direction)
        sobelx = cv2.Sobel(blurred, cv2.CV_64F, 1, 0, ksize=3)
        abs_sobelx = np.absolute(sobelx)
        sobel_8u = np.uint8(abs_sobelx / abs_sobelx.max() * 255)
        
        # Threshold the edge image
        _, thresh = cv2.threshold(sobel_8u, 50, 255, cv2.THRESH_BINARY)
        
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
        valid_contours = []
        
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # Filter for vertical edges (height > width and minimum height)
            if h > w and h >= min_height:
                valid_contours.append(contour)
                cv2.rectangle(edge_viz, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        if valid_contours:
            # Find the largest vertical edge by height
            largest_contour = max(valid_contours, key=lambda c: cv2.boundingRect(c)[3])
            x, y, w, h = cv2.boundingRect(largest_contour)
            
            # Calculate distance from left and right screen edges
            left_distance = x
            right_distance = frame.shape[1] - (x + w)
            
            # Update properties
            self.leftDistanceProp.set(left_distance)
            self.rightDistanceProp.set(right_distance)
            
            # Check if it's centered (distances should be similar)
            distance_diff = abs(left_distance - right_distance)
            if distance_diff <= self.threshold_pixels.get():
                self.isCenteredConfidently.set(True)
            else:
                self.isCenteredConfidently.set(False)
                
            # Draw the largest vertical edge
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            cv2.putText(
                frame, 
                f"L: {left_distance}px, R: {right_distance}px", 
                (10, 30), 
                cv2.FONT_HERSHEY_SIMPLEX, 
                0.7, 
                (0, 255, 0), 
                2
            )
            
            # Draw all valid vertical edges in the visualization
            cv2.drawContours(edge_viz, valid_contours, -1, (0, 0, 255), 2)
            
        else:
            self.leftDistanceProp.set(-1)
            self.rightDistanceProp.set(-1)
            self.isCenteredConfidently.set(False)
            
        # If showing frames is enabled, display the edge visualization
        if self.showFrames:
            cv2.imshow("Vertical Edges", edge_viz)
            
    def getName(self) -> str:
        return "VerticalEdgeAlignmentCheck"
        
    def getDescription(self) -> str:
        return "Detects-Vertical-Edges-For-AprilTag-Alignment"


def partialVerticalAlignmentCheck(showFrames: bool = False):
    return partial(VerticalAlignmentChecker, showFrames=showFrames)