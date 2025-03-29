import cv2

import numpy as np


def getReefAlignEstimates(frame: np.ndarray, hist):
    midFrame = frame.shape[1]//2
    lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
    backProj = cv2.calcBackProject([lab], [1, 2], hist, [0, 256, 0, 256], 1)

    # left side ========
    left = -1

    backProj_left = backProj[:,:midFrame]
    cv2.imshow("backl",backProj_left)

    _, thresh = cv2.threshold(backProj_left, 80, 255, type=cv2.THRESH_BINARY)
    erode_big = cv2.erode(thresh, np.ones((3,3)), iterations=10)
    dil_big = cv2.dilate(erode_big, np.ones((3,3)), iterations=10)

    contours, _ = cv2.findContours(dil_big, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if contours:
        biggest = max(contours, key=lambda c : cv2.boundingRect(c)[3])
        cv2.drawContours(frame, [biggest], -1, (0, 0, 255), 2)
        x,y,w,h = cv2.boundingRect(biggest)
        left = abs(x-midFrame)

    # right side ========
    right = -1

    backProj_right = backProj[:,midFrame:]
    cv2.imshow("backr",backProj_right)

    _, thresh = cv2.threshold(backProj_right, 30, 255, type=cv2.THRESH_BINARY)
    erode_big = cv2.erode(thresh, np.ones((3,3)), iterations=3)
    dil_big = cv2.dilate(erode_big, np.ones((3,3)), iterations=5)

    contours, _ = cv2.findContours(dil_big, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
    if contours:
        biggest = max(contours, key=lambda c : cv2.boundingRect(c)[3])
        shifted_biggest = biggest + np.array([midFrame, 0])
        cv2.drawContours(frame, [shifted_biggest], -1, (0, 0, 255), 2)
        x,y,w,h = cv2.boundingRect(shifted_biggest)
        right = abs(x-midFrame)


    cv2.putText(frame, f"L: {left} R: {right}", (10,20), 1, 1, (255, 255, 255))


    cv2.imshow("out",frame)


if __name__ == "__main__":
    hist = np.load("assets/stingerHistogram.npy")
    
    cap = cv2.VideoCapture(1)

    while cap.isOpened():
        ret, frame = cap.read()

        getReefAlignEstimates(frame, hist)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()