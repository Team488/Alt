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
import KobesAStar

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mapDemos.probmap import ProbMap

robotSizeX = 3
robotSizeY = 3
objSize = 35
# fieldX = 130
# fieldY = 65
fieldX = 651
fieldY = 323
res = 1

wX = int(fieldX / 3) 
wY = int(fieldY / 3)

# defaultRobotX = int(fieldX/2) # 65 800
# defaultRobotY = int(fieldY/2) # 32 400

defaultRobotX = int(fieldX/2) # 65
defaultRobotY = int(fieldY/2) # 32

map = ProbMap(
    fieldX, fieldY, res, objSize, objSize, robotSizeX, robotSizeY
) 

locked_on = False
locked_on_targets = None
initial_target = None

obstacles = [(random.randint(0, fieldY - 1), random.randint(0, fieldX - 1)) for _ in range(200)]

# def onPressSpawnGameObj(event, x, y, flags, param):
#     if event == cv2.EVENT_LBUTTONDOWN:
#         probability = random.randint(1, 10) / 10
#         map.addCustomObjectDetection(x, y, 200, 200, probability, 1)

def spawnGameObj():
    probability = random.randint(1, 10) / 10
    randomX = random.randint(0, fieldX)
    randomY = random.randint(0, fieldY)

    map.addCustomObjectDetection(randomX, randomY, 120, 120, probability, 1)

def getDistanceBetweenTwo(x1, y1, x2, y2):
    return math.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)

# def arrangeDistance(robotX, robotY, robotCoords):

#     if not robotCoords:
#         print("No objects detected currently")
#         return 

#     closest_detection = robotCoords[0]
#     closest_distance = getDistanceBetweenTwo(robotX, robotY, closest_detection[0], closest_detection[1])

#     for detection in robotCoords[1:]:
#         distance = getDistanceBetweenTwo(robotX, robotY, detection[0], detection[1])
#         if distance < closest_distance:
#             closest_detection = detection
#             closest_distance = distance

#     return closest_detection[:2]

def arrangeDistance(robotX, robotY, robotCoords):
    if not robotCoords:
        print("No objects detected currently")
        return []

    # Sort the robotCoords based on the distance to the robot
    sorted_coords = sorted(robotCoords, key=lambda detection: getDistanceBetweenTwo(robotX, robotY, detection[0], detection[1]))

    return sorted_coords

def lockOnTarget(robotCoords):   
    global locked_on
    global locked_on_targets
    global initial_target

    locked_on_targets = robotCoords
    initial_target = robotCoords[0]
    
    # if not locked_on_targets:
    #     print("No objects detected, cannot lock on right now!")
    # else:
    #     path = findPath(initial_target)

    #     if path:
    #         print("You have locked onto the closest object at " + str(initial_target) + "!")
    #         print(f"Path: {path}") 
    #         displayPathMap((defaultRobotX, defaultRobotY), initial_target, path)
    #     else:
    #         initial_target = robotCoords[1]

    #         path = findPath(initial_target)

    #         if path:
    #             print("You have locked onto the closest available object at " + str(initial_target) + "!")
    #             print(f"Path: {path}") 
    #             displayPathMap((defaultRobotX, defaultRobotY), initial_target, path)

    if not locked_on_targets:
        print("No objects detected, cannot lock on right now!")
    else:
        # Try to lock onto the initial target
        path = findPath(initial_target)

        if path:
            print()
            print("You have locked onto the closest object at " + str(initial_target) + "!")
            print(f"Path: {path}") 
            displayPathMap((defaultRobotX, defaultRobotY), initial_target, path)
        else:
            for target in robotCoords[1:]:  
                path = findPath(target)
                if path:
                    initial_target = target
                    print()
                    print("You have locked onto the closest available object at " + str(initial_target) + "!")
                    print()
                    print(f"Path: {path}") 
                    displayPathMap((defaultRobotX, defaultRobotY), initial_target, path)
                    break  
            else:
                print("No available objects to lock onto.")
                
        locked_on = True

def findPath(TARGET):
    ROBOT_LOCATION = defaultRobotX, defaultRobotY

    path = KobesAStar.a_star_search((defaultRobotX, defaultRobotY), TARGET, set(obstacles), fieldX, fieldY)

    if path: 
        return path
    else:
        print()
        print(f"No path available for: {TARGET}")
        return
        
def displayPathMap(ROBOT_LOCATION, TARGET, PATH):
    KobesAStar.display_map(fieldX, fieldY, ROBOT_LOCATION, TARGET, obstacles, PATH)
    
cv2.namedWindow(map.gameObjWindowName)
# cv2.setMouseCallback(map.gameObjWindowName, spawnGameObj)

def loop():
    while True:
        map.disspateOverTime(1)
        map.displayHeatMaps()

        (objMap, roboMap) = map.getHeatMaps()

        cv2.imshow(map.gameObjWindowName, objMap)

        if not locked_on:
            spawnGameObj()

        key = cv2.waitKey(100) & 0xFF 
        if key == ord("q"): 
            break
        if key == ord("c"):
            map.clear_maps()
        if key == ord("-"):
            targets = map.getAllGameObjectsAboveThreshold(0.1)
            
            robotCoords = [(x, y) for x, y, _, _ in targets]
            print(robotCoords)
            print(arrangeDistance(defaultRobotX, defaultRobotY, robotCoords))

            lockOnTarget(arrangeDistance(defaultRobotX, defaultRobotY, robotCoords))

            # lockOnTarget()
loop()
