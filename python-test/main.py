import probmap
import random
import traceback
import socket
import numpy as np
import struct

# import ntcore as nt


def main():
    fieldMap = probmap.ProbMap(1654, 821, 1)  # Width x Height at 1 cm resolution

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

    test_run()


# randomizes values for stress testing algorithm
def test_run():
    fieldMap = probmap.ProbMap(1654, 821, 1)  # Width x Height at 1 cm resolution
    fieldMap.display_map()
    for i in range(200):
        # fieldMap.add_detection(300, 150, 250, 250, 0.5)
        fieldMap.smooth()
        test_randomization_ranges(
            fieldMap, fieldMap.get_shape()[0], fieldMap.get_shape()[1]
        )
        fieldMap.display_map()
        # fieldMap.clear_map()


def test_randomization_ranges(map, width, height):
    for i in range(1):
        x = random.randrange(0, width)
        y = random.randrange(0, height)
        obj_size = 36 * 6  # size*total potential STD #random.randrange(36, 36)
        confidence = (
            random.randrange(35, 99, 1) / 100
        )  # generates a confidence threshold between 0.35 - 0.99
        try:
            map.add_detection(x, y, obj_size, obj_size, confidence)
        except Exception:
            traceback.print_exc()


if __name__ == "__main__":
    main()
