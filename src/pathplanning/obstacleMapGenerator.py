import numpy as np
import cv2
from tools.Constants import MapConstants

isLButtonDown = False


def startGeneration():
    mapPath = "assets/obstacleMap.npy"
    windowName = "Map Generator"
    heightTrackbarName = "Max Height in CM"
    brushTrackbarName = "Brush Size"
    map = (
        np.ones(
            (MapConstants.fieldHeight.value, MapConstants.fieldWidth.value),
            dtype=np.uint8,
        )
        * 255
    )
    try:
        map = np.load(mapPath)
    except Exception:
        print("failed to load any saved map")

    cv2.namedWindow(windowName)

    def n(x):
        pass

    cv2.createTrackbar(heightTrackbarName, windowName, 50, 255, n)
    cv2.createTrackbar(brushTrackbarName, windowName, 6, 40, n)

    def displayCallback(event, x, y, flags, param):
        global isLButtonDown
        if event == cv2.EVENT_LBUTTONDOWN:
            isLButtonDown = True
            print("clicked!")
            heightValue = cv2.getTrackbarPos(heightTrackbarName, windowName)
            radius = cv2.getTrackbarPos(brushTrackbarName, windowName)
            cv2.circle(map, (x, y), radius, (heightValue), -1)
        elif event == cv2.EVENT_LBUTTONUP:
            isLButtonDown = False
        elif isLButtonDown:
            heightValue = cv2.getTrackbarPos(heightTrackbarName, windowName)
            radius = cv2.getTrackbarPos(brushTrackbarName, windowName)
            cv2.circle(map, (x, y), radius, (heightValue), -1)

    cv2.setMouseCallback(windowName, displayCallback)

    while True:
        mapCopy = cv2.merge((map.copy(), map.copy(), map.copy()))
        cv2.putText(
            mapCopy, "S-> Save | R-> Reset | Q-> Quit", (5, 15), 1, 2, (0, 255, 0), 1
        )
        cv2.imshow(windowName, mapCopy)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            map = (
                np.ones(
                    (MapConstants.fieldHeight.value, MapConstants.fieldWidth.value),
                    dtype=np.uint8,
                )
                * 255
            )
        elif key == ord("s"):
            try:
                np.save(mapPath, map)
            except FileNotFoundError:
                print("Not able to save map! Are you in the src directory?")


if __name__ == "__main__":
    startGeneration()
