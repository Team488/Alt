import cv2
import numpy as np
from abstract.AlignmentProvider import AlignmentProvider
from Core import getChildLogger
from Core.ConfigOperator import staticLoad

Sentinel = getChildLogger("DocTr_Alignment_Provider")


class ReefPostAlignmentProvider(AlignmentProvider):
    def __init__(self):
        super().__init__()

    def create(self):
        super().create()
        self.hist, self.mtime = staticLoad(
            "assets\stingerHistogram.npy", isRelativeToSource=True
        )
        self.threshold = self.propertyOperator.createProperty("Reef_Post_Threshold", 60)
        self.erosioniter = self.propertyOperator.createProperty("Reef_Erosion_iter", 1)
        self.dilationiter = self.propertyOperator.createProperty("Reef_Dilation_iter", 2)
        self.kernelSize = self.propertyOperator.createProperty("SquareKernelLength",3)

    def isColorBased(self):
        return True  # HAS to be color

    def align(self, frame, draw):
        if not self.checkFrame(frame):
            raise ValueError("The frame is not a color frame!")

        fourth = frame.shape[1]//4
        cut1 = fourth
        cut2 = 3*fourth

        focused = frame[:,cut1:cut2] #clip roi
    

        lab = cv2.cvtColor(focused, cv2.COLOR_BGR2LAB)

        backProj = cv2.calcBackProject([lab], [1, 2], self.hist, [0, 256, 0, 256], 1)


        _, thresh = cv2.threshold(backProj, self.threshold.get(), 255, type=cv2.THRESH_BINARY)
        ksize = self.kernelSize.get()
        erode_big = cv2.erode(thresh, np.ones((ksize, ksize)), iterations=self.erosioniter.get())
        dil_big = cv2.dilate(erode_big, np.ones((ksize, ksize)), iterations=self.dilationiter.get())

        contours, _ = cv2.findContours(
            dil_big, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE
        )

        left, right, m = None, None, None
        if contours:
            biggest = max(contours, key=lambda c: cv2.boundingRect(c)[3])
            if draw:
                cv2.drawContours(frame, [biggest], -1, (0, 0, 255), 2)
            x, y, w, h = cv2.boundingRect(biggest)

            left = x
            right = x+w
            m = (left+right)/2
            

        if draw:
            cv2.putText(frame, f"L: {left} R: {right} M: {m}", (10, 20), 1, 1, (255))

        return left, right
