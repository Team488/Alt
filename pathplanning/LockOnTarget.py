"""
    Goals for this class
    Given a target XYCoord, save the coordinate and have the robot "lock on" to it. 
    The important part is to check the map when it is updated to see if the target is still there / Probability above a threshold
    EX: Asked to lock on to a note at (50,50) while it is above 75% chance of being there. When they ask for the target, you give them this target until one check where the target probability drops below 75%
    Now you have to reroute as your target has dissapeared, so find the new closest target.

    Known Data: Probablity maps, target coordinates (Also found through the map)
    Expected output: An XY coord that is the target position until it goes away. Once that happens you should retarget to the next best coordinate and send that out

"""
import sys
import os
import cv2
import random
import time
import math 

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'map-tests')))
import probmap

robotSizeX = 60
robotSizeY = 90
objSize = 35
fieldX = 1600  
fieldY = 1000  
res = 1 

wX = int(fieldX / 3)
wY = int(fieldY / 3)

map = probmap.ProbMap(
    fieldX, fieldY, res, objSize, objSize, robotSizeX, robotSizeY
) 

def onPressSpawnGameObj(event, x, y, flags, param):
    if event == cv2.EVENT_LBUTTONDOWN:
        probability = random.randint(1, 10) / 10
        map.addCustomObjectDetection(x, y, 200, 200, probability, 1)

def getDistanceBetweenTwo(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

def getClosestDetectionAboveThreshold(robotX, robotY):
    detections = map.getAllGameObjectsAboveThreshold(0.4)

    if not detections:
        print("No objects detected currently")
        return None

    closest_detection = detections[0]
    closest_distance = getDistanceBetweenTwo(robotX, robotY, closest_detection[0], closest_detection[1])

    for detection in detections[1:]:
        distance = getDistanceBetweenTwo(robotX, robotY, detection[0], detection[1])
        if distance < closest_distance:
            closest_detection = detection
            closest_distance = distance

    print("Closest distance: " + str(closest_distance))
    print("Object closest: " + str(closest_detection[:2]))

cv2.namedWindow(map.gameObjWindowName)
cv2.setMouseCallback(map.gameObjWindowName, onPressSpawnGameObj)

def loop():
    # center of field robot spawn position
    defaultRobotX = int(fieldX/2)
    defaultRobotY = int(fieldY/2)

    while True:
        map.disspateOverTime(1)
        map.displayHeatMaps()

        (objMap, robotMap) = map.getHeatMaps()

        cv2.imshow(map.gameObjWindowName, objMap)

        getClosestDetectionAboveThreshold(defaultRobotX, defaultRobotY)

        k = cv2.waitKey(100) & 0xFF 
        if k == ord("q"):
            break
        if k == ord("c"):
            map.clear_maps()

loop()