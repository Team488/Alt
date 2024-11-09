import os
import sys
import cv2
import random
import numpy as np


from PathGenerator import PathGenerator
from PathFind import PathFinder



robotSizeX = 3
robotSizeY = 3
objSize = 35

fieldX = 1000
fieldY = 600
res = 1
wX = int(fieldX / 5)
wY = int(fieldY / 5)

defaultRobotX = 100
defaultRobotY = 500

defaultGoalX = 900
defaultGoalY = 100
radius = 10

obstacles_list = []

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mapinternals.probmap import ProbMap as probmap

map = probmap(
    fieldX, fieldY, res, objSize, objSize, robotSizeX, robotSizeY
)

(objMap, roboMap) = map.getHeatMaps()

path_finder_instance = PathFinder(fieldX, fieldY)


# def spawnObstacles(event, x, y, flags, param):
#     # x = random.randint(0, fieldX)
#     # y = random.randint(0, fieldY)

#     if event == cv2.EVENT_LBUTTONDOWN:
#         cv2.rectangle(
#             roboMap,
#             (
#                 int(x - wX / 12) // map.resolution,
#                 int(y - wY / 12) // map.resolution,
#             ),
#             (
#                 int(x + wX / 12) // map.resolution,
#                 int(y + wY / 12) // map.resolution,
#             ),
#             (255),
#             2,
#         )

def spawnObstacles(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        # Calculate obstacle position based on click
        x1 = int(x - wX / 12) // map.resolution
        y1 = int(y - wY / 12) // map.resolution
        x2 = int(x + wX / 12) // map.resolution
        y2 = int(y + wY / 12) // map.resolution

        obstacles_list.append((x1, y1))
        
        cv2.rectangle(roboMap, (x1, y1), (x2, y2), (255), 2)


def draw_robot(image, x, y, wX, wY):
    pt1 = (int(x) // map.resolution, int(y - wY / 12) // map.resolution)
    pt2 = (int(x - wX / 12) // map.resolution, int(y + wY / 12) // map.resolution)
    pt3 = (int(x + wX / 12) // map.resolution, int(y + wY / 12) // map.resolution)
    
    triangle_cnt = np.array([pt1, pt2, pt3])
    
    cv2.fillPoly(image, [triangle_cnt], (255))


def draw_goal(image, x, y, radius):
     cv2.circle(image, (x, y), radius, (255, 255, 255), -1)


cv2.namedWindow(map.robotWindowName)
cv2.setMouseCallback(map.robotWindowName, spawnObstacles)

def loop():
    while True:
        draw_robot(roboMap, defaultRobotX, defaultRobotY, wX, wY)
        draw_goal(roboMap, defaultGoalX, defaultGoalY, radius)
        map.displayHeatMaps()

        cv2.imshow(map.robotWindowName, roboMap)
        
        key = cv2.waitKey(100) & 0xFF
        if key == ord("q"):
            break
        if key == ord("c"):
            map.clear_maps()
        if key == ord("-"):
            print("BRo")
            print(obstacles_list)
            print((defaultRobotX,defaultRobotY))
            print((defaultGoalX, defaultGoalY))
            path_finder_instance.update_path_with_values((defaultRobotX, defaultRobotY), (defaultGoalX, defaultGoalY), obstacles_list, 10000)
            # path_finder_instance.a_star_search((defaultRobotX, defaultRobotY), (defaultGoalX, defaultGoalY), obstacles_list, fieldX, fieldY)

loop()