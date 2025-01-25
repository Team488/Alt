import numpy as np
import cv2
from tools.Constants import MapConstants

isLButtonDown = False


def startGeneration():
    mapPath = "assets/obstacleMap.npy"
    fieldPath = "assets/fieldTopDown.png"
    fieldMap = None
    try:
        fieldMap = cv2.imread(fieldPath)
        fieldMap = cv2.resize(fieldMap,(MapConstants.fieldWidth.value, MapConstants.fieldHeight.value))
    except Exception:
        print("failed to load any saved field map")
        fieldMap = (
            np.ones(
                (MapConstants.fieldHeight.value, MapConstants.fieldWidth.value),
                dtype=np.uint8
            )
            * 255
        )
    

    windowName = "Map Generator"
    brushTrackbarName = "Brush Size"
    draw_map = np.zeros(
            (MapConstants.fieldHeight.value, MapConstants.fieldWidth.value),
            dtype=bool
        )
    

    try:
        draw_map = np.load(mapPath)
    except Exception:
        print("failed to load any saved map")


    cv2.namedWindow(windowName)

    def n(x):
        pass

    cv2.createTrackbar(brushTrackbarName, windowName, 6, 40, n)

    def displayCallback(event, x, y, flags, param):
        global isLButtonDown
        nonlocal draw_map
        if event == cv2.EVENT_LBUTTONDOWN:
            isLButtonDown = True
            print("clicked!")
            radius = cv2.getTrackbarPos(brushTrackbarName, windowName)
            draw_map = draw_map.astype(dtype=np.uint8)
            cv2.circle(draw_map, (x, y), radius, (1), -1)
            draw_map = draw_map.astype(dtype=bool)
        elif event == cv2.EVENT_LBUTTONUP:
            isLButtonDown = False
        elif isLButtonDown:
            radius = cv2.getTrackbarPos(brushTrackbarName, windowName)
            draw_map = draw_map.astype(dtype=np.uint8)
            cv2.circle(draw_map, (x, y), radius, (1), -1)
            draw_map = draw_map.astype(dtype=bool)

    cv2.setMouseCallback(windowName, displayCallback)

    while True:
        mapCopy = cv2.merge((draw_map.copy().astype(dtype=np.uint8)*255, draw_map.copy().astype(dtype=np.uint8)*255, draw_map.copy().astype(dtype=np.uint8)*255))
        print(f"Map Shape: {mapCopy.shape} FieldMap Shape: {fieldMap.shape}")
        mapCopy = cv2.bitwise_or(mapCopy,fieldMap)
        cv2.putText(
            mapCopy, "S-> Save | R-> Reset | Q-> Quit", (5, 25), 1, 2, (0, 255, 0), 1
        )
        cv2.imshow(windowName, mapCopy)
        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break
        elif key == ord("r"):
            draw_map = (
                np.zeros(
                    (MapConstants.fieldHeight.value, MapConstants.fieldWidth.value),
                    dtype=bool
                )
            )
        elif key == ord("s"):
            try:
                np.save(mapPath, draw_map)
            except FileNotFoundError:
                print("Not able to save map! Are you in the src directory?")


if __name__ == "__main__":
    startGeneration()
