from mapinternals.probmap import ProbMap
import cv2

res = 1  # cm
# object and robot values not necessary here
map = ProbMap(2000, 1000, res, 100, 100, 1000, 1000)

isMouseDownG = False
isMouseDownR = False


def mouseDownCallbackGameObj(event, x, y, flags, param):
    global isMouseDownG
    if event == cv2.EVENT_LBUTTONDOWN:
        isMouseDownG = True
        #  print("clicked at ", x," ", y)
        map.addCustomObjectDetection(
            x, y, 200, 200, 0.75, 1
        )  # adding as a 75% probability
    elif event == cv2.EVENT_MOUSEMOVE:
        if isMouseDownG:
            #   print("dragged at ", x," ", y)
            map.addCustomObjectDetection(
                x, y, 200, 200, 0.75, 1
            )  # adding as a 75% probability
    elif event == cv2.EVENT_LBUTTONUP:
        isMouseDownG = False


def mouseDownCallbackRobot(event, x, y, flags, param):
    global isMouseDownR
    if event == cv2.EVENT_LBUTTONDOWN:
        isMouseDownR = True
        #  print("clicked at ", x," ", y)
        map.addCustomRobotDetection(
            x, y, 200, 200, 0.75, 1
        )  # adding as a 75% probability
    elif event == cv2.EVENT_MOUSEMOVE:
        if isMouseDownR:
            #   print("dragged at ", x," ", y)
            map.addCustomRobotDetection(
                x, y, 200, 200, 0.75, 1
            )  # adding as a 75% probability
    elif event == cv2.EVENT_LBUTTONUP:
        isMouseDownR = False


def startDemo():
    cv2.namedWindow(map.gameObjWindowName)
    cv2.setMouseCallback(map.gameObjWindowName, mouseDownCallbackGameObj)

    cv2.namedWindow(map.robotWindowName)
    cv2.setMouseCallback(map.robotWindowName, mouseDownCallbackRobot)  # get mouse event
    while True:
        map.disspateOverTime(5)  # 1s
        map.displayHeatMaps()
        print("Best game obj:", map.getHighestGameObject())
        print("Best robot:", map.getHighestRobot())

        k = cv2.waitKey(100) & 0xFF
        if k == ord("q"):
            break
        if k == ord("c"):
            map.clear_maps()


if __name__ == "__main__":
    startDemo()
