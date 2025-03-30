import time
import cv2
import numpy as np
from abstract.AlignmentProvider import AlignmentProvider
from Core import getChildLogger
from Core.ConfigOperator import staticLoad
from tools import generalutils

Sentinel = getChildLogger("DocTr_Alignment_Provider")


class ReefPostAlignmentProvider(AlignmentProvider):
    def __init__(self):
        super().__init__()

    def create(self):
        super().create()
        self.hist, self.mtime = staticLoad(
            "assets/histograms/reef_post_hist.npy", isRelativeToSource=True
        )
        self.threshold = self.propertyOperator.createProperty("Reef_Post_Thresh", 150)
        self.roi = self.propertyOperator.createProperty("Roi", 0.5)
        self.minLineLength = self.propertyOperator.createProperty("MinLinelength", 50)
        self.angleRange = self.propertyOperator.createProperty("Angle_Range",10)
        self.propertyOperator.createReadOnlyProperty("Histogram_Update_Time", generalutils.getTimeStr(time.localtime(self.mtime)))

    def isColorBased(self):
        return True  # HAS to be color

    def align(self, frame, draw):
        if not self.checkFrame(frame):
            raise ValueError("The frame is not a color frame!")

        half = frame.shape[1]//2
        roi = int(half * self.roi.get())
        cut1 = half-roi
        cut2 = half+roi

        focused = frame[:,cut1:cut2] #clip roi
    

        lab = cv2.cvtColor(focused, cv2.COLOR_BGR2LAB)

        backProj = cv2.calcBackProject([lab], [1, 2], self.hist, [0, 256, 0, 256], 1)


        _, thresh = cv2.threshold(backProj, self.threshold.get(), 255, type=cv2.THRESH_BINARY)

        sobelx = cv2.Sobel(thresh, cv2.CV_64F, 1, 0, ksize=3)
        abs_sobelx = np.absolute(sobelx)
        sobel_8u = np.uint8(abs_sobelx / abs_sobelx.max() * 255)

        _, thresh = cv2.threshold(sobel_8u, self.threshold.get(), 255, cv2.THRESH_BINARY)

        # Apply morphological operations to enhance vertical edges
        kernel_vertical = np.ones((5, 1), np.uint8)
        vertical_edges = cv2.morphologyEx(thresh, cv2.MORPH_CLOSE, kernel_vertical)

        contours, _ = cv2.findContours(
            vertical_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        contours = [contour + (cut1, 0) for contour in contours]

        if draw:
            cv2.drawContours(frame, contours, -1, (255,255,255), 1)


        lines = cv2.HoughLinesP(vertical_edges, rho=1, theta=np.pi/180, threshold=50, minLineLength=30, maxLineGap=10)
        
        left, right = None, None

        bestLines = []
        if lines is not None:
            for line in lines:
                x1, y1, x2, y2 = line[0]
                avgX = (x1+x2)/2
                dist = np.linalg.norm((x2-x1,y2-y1))
                angle = np.arctan2(abs(y2 - y1), abs(x2 - x1)) * 180 / np.pi
                if dist > self.minLineLength.get() and 90-self.angleRange.get() < angle < 90+self.angleRange.get():  # Keep nearly vertical lines
                    bestLines.append(line)
                    if draw:
                        cv2.line(frame, (x1+cut1, y1), (x2+cut1, y2), (0, 255, 0), 2)

                    if left is None or left > avgX:
                        left = avgX
                    
                    if right is None or right < avgX:
                        right = avgX
        if left is not None:
            left += cut1
        if right is not None:
            right += cut1
        if draw:
            cv2.putText(frame, f"L: {left} R: {right}", (10, 20), 1, 1, (255))

        return left, right

