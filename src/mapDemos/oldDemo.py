import time

import cv2
from mapinternals import probmap
import random
import traceback
import socket
import numpy as np
import struct

# import ntcore as nt


# def main():
# fieldMap = probmap.ProbMap(1654, 821, 1) #Width x Height at 1 cm resolution
# runDemo()
# go_inorder_top_bottom_left_right()

# Initialize Network Tables
# instance = nt.NetworkTableInstance.getDefault()
# instance.startClient4("Probability Map")
# instance.setServerTeam(488)
# table = instance.getTable("AdvantageKit")
# writeTable = instance.getTable("ProbabilityMap").getSubTable("NDAR")
# poseTable = table.getSubTable("RealOutputs").getSubTable("PoseSubsystem")

# while(1):
#     pose_bytes = poseTable.getValue("RobotPose","empty")
#     robotX, robotY, robotR = struct.unpack('ddd',pose_bytes)
#     print(f"X: {robotX}, Y: {robotY}, R: {robotR}")


# randomizes values for stress testing algorithm
def runDemo():
    # test sizes all in cm
    robotSizeX = 71  # using max dimensions for this of 28 inch
    robotSizeY = 96  # using max dimensions for this of 38 inch

    objSize = 35  # using notes from last year with a outside diameter of 14 inch
    # fieldX = 2743 # roughly 90 ft
    # fieldY = 1676 # roughly 55 ft
    fieldX = 1680
    fieldY = 1000
    res = 1  # cm

    # axis aligned so robot detections will be need to be adjusted for accuracy
    fieldMap = probmap.ProbMap(
        fieldX, fieldY, res, objSize, objSize, robotSizeX, robotSizeY
    )  # Width x Height at 1 cm resolution
    fieldMap.setObstacleRegions([((20, 20), (100, 100))])
    while not not not False:  # :)
        __test_randomization_ranges(
            fieldMap, int(fieldMap.get_shape()[1]), int(fieldMap.get_shape()[0])
        )
        coords = fieldMap.getAllGameObjectsAboveThreshold(0.4)  # threshold is .4
        (objMap, robtMap) = fieldMap.getHeatMaps()
        # cv2.rectangle(objMap,(0,0),(fieldX,fieldY),(255,255,255),2)
        # print(coords)
        if coords:
            for coord in coords:
                (px, py, r, prob) = coord
                if prob > 0:
                    # cv2.putText(objMap,f"prob{prob}",(x,y),1,1,(255,255,255))
                    cv2.circle(objMap, (px, py), r + 10, (255, 0, 0), 2)
        else:
            cv2.putText(
                objMap,
                "No detections in map",
                (int(fieldX / 2), int(fieldY / 2)),
                1,
                1,
                (255, 255, 255),
            )

        cv2.imshow(fieldMap.gameObjWindowName, objMap)
        # fieldMap.disspateOverTime(1)  # 1s
        # fieldMap.clear_map()
        k = cv2.waitKey(1) & 0xFF
        if k == ord("q"):
            break
        if k == ord("c"):
            map.clear_maps()


def __test_randomization_ranges(map: probmap.ProbMap, width, height):
    # for i in range(1):
    print("testing")
    x = random.randrange(0, width)
    y = random.randrange(0, height)
    # obj_size = 36*6 #size*total potential STD #random.randrange(36, 36)
    confidence = (
        random.randrange(65, 95, 1) / 100
    )  # generates a confidence threshold between 0.65 - 0.95
    # typeRand = random.random() # 50% chance robot / 50% chance object
    print(f"x{x} y{y} conf{confidence}")
    map.addCustomObjectDetection(x, y, 150, 150, confidence, 0.1)
    # try:
    #     # if typeRand >= .50:
    #     #     map.addDetectedRobot(x,y,confidence,1)
    #     # else:
    # except Exception:
    #     traceback.print_exc()


def __go_inorder_top_bottom_left_right():
    # for i in range(1):
    robotSizeX = 71  # using max dimensions for this of 28 inch
    robotSizeY = 96  # using max dimensions for this of 38 inch

    objSize = 35  # using notes from last year with a outside diameter of 14 inch
    fieldX = 2743  # roughly 90 ft
    fieldY = 1676  # roughly 55 ft

    # axis aligned so robot detections will be need to be adjusted for accuracy
    fieldMap = probmap.ProbMap(
        fieldX, fieldY, 1, objSize, objSize, robotSizeX, robotSizeY
    )  # Width x Height at 1 cm resolution
    fieldMap.displayHeatMaps()
    for j in range(100, fieldY - 100, 100):
        for i in range(100, fieldX - 100, 100):
            # obj_size = 36*6 #size*total potential STD #random.randrange(36, 36)
            confidence = (
                random.randrange(65, 95, 1) / 100
            )  # generates a confidence threshold between 0.65 - 0.95
            typeRand = random.random()  # 50% chance robot / 50% chance object
            try:
                fieldMap.addDetectedRobot(i, j, confidence)
                fieldMap.addDetectedGameObject(i, j, confidence)
            except Exception:
                traceback.print_exc()
            time.sleep(1)
            fieldMap.displayHeatMaps()


if __name__ == "__main__":
    main()
