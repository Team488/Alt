import cv2
import numpy as np
from abstract.AlignmentProvider import AlignmentProvider
from Core import getChildLogger
from Core.ConfigOperator import staticLoad

Sentinel = getChildLogger("DocTr_Alignment_Provider")


class ReefPostAlignmentProvider(AlignmentProvider):
    def __init__(self):
        super().__init__()
        self.hist, self.mtime = staticLoad("assets\stingerHistogram.npy",isRelativeToSource=True)

    def isColorBased(self):
        return True  # HAS to be color

    def align(self, frame, draw):
        if not self.checkFrame(frame):
            raise ValueError("The frame is not a color frame!")

        midFrame = frame.shape[1] // 2
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)

        backProj = cv2.calcBackProject([lab], [1, 2], self.hist, [0, 256, 0, 256], 1)

        # left side ========
        left = -1

        # extract left side of frame
        backProj_left = backProj[:, :midFrame]

        _, thresh = cv2.threshold(backProj_left, 80, 255, type=cv2.THRESH_BINARY)
        erode_big = cv2.erode(thresh, np.ones((3, 3)), iterations=10)
        dil_big = cv2.dilate(erode_big, np.ones((3, 3)), iterations=10)

        contours, _ = cv2.findContours(
            dil_big, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )
        if contours:
            biggest = max(contours, key=lambda c: cv2.boundingRect(c)[3])
            if draw:
                cv2.drawContours(frame, [biggest], -1, (0, 0, 255), 2)
            x, y, w, h = cv2.boundingRect(biggest)
            left = abs(x - midFrame)

        # right side ========
        right = -1

        # extract right side of frame
        backProj_right = backProj[:, midFrame:]

        _, thresh = cv2.threshold(backProj_right, 30, 255, type=cv2.THRESH_BINARY)
        erode_big = cv2.erode(thresh, np.ones((3, 3)), iterations=3)
        dil_big = cv2.dilate(erode_big, np.ones((3, 3)), iterations=5)

        contours, _ = cv2.findContours(
            dil_big, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )
        if contours:
            biggest = max(contours, key=lambda c: cv2.boundingRect(c)[3])
            shifted_biggest = biggest + np.array([midFrame, 0])
            if draw:
                cv2.drawContours(frame, [shifted_biggest], -1, (0, 0, 255), 2)
            x, y, w, h = cv2.boundingRect(shifted_biggest)
            right = abs(x - midFrame)

        if draw:
            cv2.putText(frame, f"L: {left} R: {right}", (10, 20), 1, 1, (255))

            cv2.imshow("gray",gray)


        return left, right
