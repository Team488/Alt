import time

import numpy as np
import mapDemos.utils as demoUtils
from mapinternals.probmap import ProbMap
import cv2
import pathplanning.utils as pathPlanningUtils
from pathplanning.PathFind import PathFinder

res = 1
mapSizeX = 2000
mapSizeY = 1000
map = ProbMap(mapSizeX, mapSizeY, res, 100, 100, 1000, 1000)

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

    # cv2.namedWindow(map.robotWindowName)
    # cv2.setMouseCallback(map.robotWindowName, mouseDownCallbackRobot)

    pathfinder = PathFinder(mapSizeX, mapSizeY)
    dx = [1, 0, -1]
    dy = [1, 0, -1]
    our_location = (500, 200)  # start in center

    while True:
        randomVector = demoUtils.getRandomMove(
            our_location[0],
            our_location[1],
            map.width,
            map.height,
            50,
        )
        our_location = tuple(np.add(our_location, randomVector))
        map.disspateOverTime(0.2)  # 1s

        robots = map.getAllRobotsAboveThreshold(0.8)
        gampieces = map.getAllGameObjectsAboveThreshold(0.8)

        best_target = pathPlanningUtils.getBestTarget(robots, gampieces, our_location)
        display_frame = map.getGameObjectHeatMap()

        cv2.circle(display_frame, our_location, 10, (255, 255, 0), -1)
        print(len(robots))
        for robot in robots:
            cv2.circle(
                display_frame,
                (int(robot[0]), int(robot[1])),
                robot[2],
                (255, 255, 0),
                -1,
            )
        #
        if pathfinder.path is not None:
            for p in pathfinder.path:
                cv2.circle(display_frame, (int(p[0]), int(p[1])), 2, (255, 255, 0), -1)

        if best_target is not None:
            cv2.circle(
                display_frame, (best_target[0], best_target[1]), 10, (0, 255, 0), -1
            )

        if best_target is not None:
            best_target_location = (int(best_target[0]), int(best_target[1]))
            pathfinder.update_path_with_values(
                start=our_location,
                goal=best_target_location,
                obstacles=robots,
                max_path_length=5000,
            )
        else:
            pathfinder.reset()
        k = cv2.waitKey(1) & 0xFF
        if k == ord("q"):
            break
        if k == ord("c"):
            map.clear_maps()
            pathfinder.reset()
        if k == ord("a"):
            pass
        cv2.imshow(map.gameObjWindowName, display_frame)


if __name__ == "__main__":
    startDemo()
