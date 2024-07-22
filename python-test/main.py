import time
import probmap
import random
import traceback
import socket
import numpy as np
import struct
import ntcore as nt

def main():
    # fieldMap = probmap.ProbMap(1654, 821, 1) #Width x Height at 1 cm resolution
    test_run()
    # go_inorder_top_bottom_left_right()






    #Initialize Network Tables
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
def test_run():
    # test sizes all in cm
    robotSizeX = 71 # using max dimensions for this of 28 inch
    robotSizeY = 96 # using max dimensions for this of 38 inch

    objSize = 35 # using notes from last year with a outside diameter of 14 inch
    fieldX = 2743 # roughly 90 ft
    fieldY = 1676 # roughly 55 ft

    # axis aligned so robot detections will be need to be adjusted for accuracy
    fieldMap = probmap.ProbMap(fieldX, fieldY, 1,objSize,objSize,robotSizeX,robotSizeY) #Width x Height at 1 cm resolution
    fieldMap.display_maps()
    for i in range(20000):
        # fieldMap.add_detection(300, 150, 250, 250, 0.5)
        fieldMap.disspateOverTime()
        test_randomization_ranges(fieldMap, int(fieldMap.get_shape()[0]), int(fieldMap.get_shape()[1]))
        if(i % 2 == 0):
            fieldMap.disspateOverTime()
        fieldMap.display_maps()
        # fieldMap.clear_map()

def test_randomization_ranges(map : probmap, width, height):
    #for i in range(1):
    x = random.randrange(0, width)
    y = random.randrange(0, height)
    # obj_size = 36*6 #size*total potential STD #random.randrange(36, 36) 
    confidence = random.randrange(65, 95, 1)/100 # generates a confidence threshold between 0.65 - 0.95
    typeRand = random.random() # 50% chance robot / 50% chance object
    try:
        if typeRand >= .50:
            map.addDetectedRobot(x,y,confidence)
        else:
            map.addDetectedGameObject(x,y,confidence)
    except Exception:
        traceback.print_exc()

def go_inorder_top_bottom_left_right():
    #for i in range(1):
    robotSizeX = 71 # using max dimensions for this of 28 inch
    robotSizeY = 96 # using max dimensions for this of 38 inch

    objSize = 35 # using notes from last year with a outside diameter of 14 inch
    fieldX = 2743 # roughly 90 ft
    fieldY = 1676 # roughly 55 ft

    # axis aligned so robot detections will be need to be adjusted for accuracy
    fieldMap = probmap.ProbMap(fieldX, fieldY, 1,objSize,objSize,robotSizeX,robotSizeY) #Width x Height at 1 cm resolution
    fieldMap.display_maps()
    for j in range(100,fieldY-100,100):
        for i in range(100,fieldX-100,100):
            # obj_size = 36*6 #size*total potential STD #random.randrange(36, 36) 
            confidence = random.randrange(65, 95, 1)/100 # generates a confidence threshold between 0.65 - 0.95
            typeRand = random.random() # 50% chance robot / 50% chance object
            try:
                fieldMap.addDetectedRobot(i,j,confidence)
                fieldMap.addDetectedGameObject(i,j,confidence)
            except Exception:
                traceback.print_exc()
            time.sleep(1)
            fieldMap.display_maps()




if __name__ == "__main__":
    main()
    
    
