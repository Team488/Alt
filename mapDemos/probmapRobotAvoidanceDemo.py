import traceback

import probmap
import random
import cv2
import math

# test sizes all in cm
robotSizeX = 71
robotSizeY = 96
objSize = 35
fieldX = 1600  # roughly 90 ft
fieldY = 1000  # roughly 55 ft
res = 1  # cm

wX = int(fieldX / 3)
wY = int(fieldY / 3)

maxDist1Sec = 10  # cm

# values other than field x,y not used in this demo
fieldMap = probmap.ProbMap(
    fieldX,
    fieldY,
    res,
    objSize,
    objSize,
    robotSizeX,
    robotSizeY,
    maxSpeedRobots=maxDist1Sec,
)  # Width x Height at 1 cm resolution

maxRobotSpeed = 60  # cm/s
objectsCollected = 0
lastCollectedX = -1
lastCollectedY = -1

deltaM = 0.4
deltaB = 1


def __check_and_get_collision_coords(
    robotStartX,
    robotStartY,
    robotGoalX,
    robotGoalY,
    obstacleStartX,
    obstacleStartY,
    obstacleGoalX,
    obstacleGoalY,
) -> tuple[int, int]:
    if robotStartX == robotGoalX:
        # Robot path is vertical so slope is infinity
        robot_slope = float("inf")
        robot_intercept = robotStartX
    else:
        robot_slope = (robotGoalY - robotStartY) / (robotGoalX - robotStartX)
        robot_intercept = robotStartY - robot_slope * robotStartX

    if obstacleStartX == obstacleGoalX:
        # Obstacle path is vertical
        obstacle_slope = float("inf")
        obstacle_intercept = obstacleStartX
    else:
        obstacle_slope = (obstacleGoalY - obstacleStartY) / (
            obstacleGoalX - obstacleStartX
        )
        obstacle_intercept = obstacleStartY - obstacle_slope * obstacleStartX

    if abs(robot_slope - obstacle_slope) < deltaM:
        # Slopes are approximately the same
        if abs(robot_intercept - obstacle_intercept) < deltaB:
            # Roughly the same line equation
            return (robotStartX, robotStartY)
        else:
            # Roughly parallel but different intercepts, so no intersection
            return None
    else:
        if robot_slope == float("inf"):
            # Intersection with vertical robot path
            x = robotStartX
            y = obstacle_slope * x + obstacle_intercept
        elif obstacle_slope == float("inf"):
            # Intersection with vertical obstacle path
            x = obstacleStartX
            y = robot_slope * x + robot_intercept
        else:
            # Regular intersection
            x = (obstacle_intercept - robot_intercept) / (robot_slope - obstacle_slope)
            y = robot_slope * x + robot_intercept

        if min(robotStartX, robotGoalX) <= x <= max(robotStartX, robotGoalX) and min(
            robotStartY, robotGoalY
        ) <= y <= max(robotStartY, robotGoalY):
            # collision in the range of robots path``
            return (x, y)
        else:
            return None


def __calcTime(cx, cy, nx, ny, vx, vy) -> float:
    dx = abs(nx - cx)
    dy = abs(ny - cy)
    if vx == 0 and vy == 0:
        return float("inf")
    if vx == 0:
        if dx == 0:
            return dy / vy
        else:
            return float("inf")

    if vy == 0:
        if dy == 0:
            return dx / vx
        else:
            return float("inf")
    tx = dx / vx
    ty = dy / vy
    return tx + ty


colisionsDetected = 0
timeDelta = 1  # 1s


def __getNextMove(cx, cy, goalX, goalY, time) -> tuple[int, int]:
    global colisionsDetected
    # # reset collisions detected
    # colisionsDetected = 0

    maxDistance = maxRobotSpeed * time
    dx = goalX - cx
    dy = goalY - cy
    mag = math.sqrt(dx**2 + dy**2)
    if mag > maxDistance:
        # rescale vectors as you are too far away to go in one step
        # unitize vectors
        dx /= mag
        dy /= mag
        # scale by max distance
        dx *= maxDistance
        dy *= maxDistance
        mag = maxDistance

    # now we need to check if any obstacles will be in our way
    preds = fieldMap.getRobotMapPredictions(time)
    for prediction in preds:
        (curPx, curPy, newPx, newPy, vx, vy, prob) = prediction
        # for each prediction, check if collision is possible
        collision = __check_and_get_collision_coords(
            cx, cy, cx + dx, cy + dy, curPx, curPy, newPx, newPy
        )
        if collision is not None:

            (collisionX, collisionY) = collision
            # first check if both robot + obstacle reach the collision around the same time
            # calculate new dx dy to avoid collision
            obstacleTimeToC = __calcTime(curPx, curPy, newPx, newPy, vx, vy)

            robotTimeToC = mag / maxRobotSpeed
            print("obstacleTimeToC:", obstacleTimeToC)
            print("robotTimeToC:", robotTimeToC)
            if abs(obstacleTimeToC - robotTimeToC) < timeDelta:
                colisionsDetected += 1

                # collision likely
                # we can try to avoid many ways but one way is to adjust our move by the opposite of the objects velocity, scaled a bit of course
                """ This code should be changed (we need to test and find the best dodging alg)"""
                safeOffsetDx = timeDelta * 1.1 * -vx
                safeOffsetDy = timeDelta * 1.1 * -vy
                dx += safeOffsetDx
                dy += safeOffsetDy

    return (int(dx), int(dy))


# robot will try to go back and forth
def __flipGoalToOtherSide(goalX):
    if goalX == 0:
        goalX = fieldX - 1
    else:
        goalX = 0
    return goalX


def __generateRobotPositions(nRobots, fieldX, fieldY) -> list[int, int]:
    curRobots = []
    for i in range(1, nRobots + 1):
        curRobots.append((100 * i, int(fieldY / 2)))
    return curRobots


def startDemo():
    # default starting position for robot is left side of the field
    robotX = 0
    robotY = int(fieldY / 2)

    goalX = fieldX - 1
    goalY = int(fieldY / 2)
    currentRobots = __generateRobotPositions(10, fieldX, fieldY)  # 10 random robots

    time = 1  # 1s for now
    print(fieldX, fieldY)
    while True:
        for i in range(20000):
            # move around sim robot detections
            __addRandomRobotsMovingAround(fieldMap, fieldX, fieldY, currentRobots)
            # get heatmap + velocity map to display
            velocityMap = fieldMap.getRobotMapPredictionsAsHeatmap(time)
            (objMap, robotMap) = fieldMap.getHeatMaps()

            mergedMap = cv2.bitwise_or(velocityMap, robotMap)

            # move own robot
            (dx, dy) = __getNextMove(robotX, robotY, goalX, goalY, time)
            robotX += dx
            robotY += dy
            if abs(robotX - goalX) < 5:
                # now start moving to the other side
                goalX = __flipGoalToOtherSide(goalX)
            # print(robotX)
            cv2.circle(mergedMap, (robotX, robotY), 4, (255), -1)
            global colisionsDetected
            cv2.putText(
                mergedMap, f"Collisions Pred:{colisionsDetected}", (10, 40), 1, 1, (255)
            )

            cv2.imshow("map", mergedMap)

            # clear
            fieldMap.clear_maps()

            k = cv2.waitKey(1000) & 0xFF
            if k == ord("q"):
                return
            if k == ord("c"):
                fieldMap.clear_maps()
            # fieldMap.clear_map()


def __myRandom(random, a, b):
    return a + random * (b - a)


def __getRandomMove(
    robotX, robotY, fieldX, fieldY, maxDistancePerMove
) -> tuple[int, int]:
    randDist = random.randint(int(maxDistancePerMove / 2), maxDistancePerMove)
    randAng = __myRandom(random.random(), 0, 2 * math.pi)
    randDx = math.cos(randAng) * randDist
    randDy = math.sin(randAng) * randDist
    # handle clipping
    safetyoffset = 2
    if robotX + randDx > fieldX:
        randDx = fieldX - robotX - safetyoffset
    if robotX + randDx < 0:
        randDx = robotX + safetyoffset
    if robotY + randDy > fieldY:
        randDy = fieldY - robotY - safetyoffset
    if robotY + randDy < 0:
        randDy = robotY + safetyoffset

    return (int(randDx), int(randDy))


def __getUpOrDown(robotX, robotY, maxDistancePerMove) -> tuple[int, int]:
    randDist = random.randint(int(maxDistancePerMove / 2), maxDistancePerMove)
    ref = int(fieldY / 2)
    if robotY > ref:
        return (0, -randDist)
    else:
        return (0, randDist)


# simulate robots moving around
def __addRandomRobotsMovingAround(
    map: probmap.ProbMap, width, height, currentRobotsAndPositions: list
):
    newDetections = []
    for i in range(len(currentRobotsAndPositions)):
        (robotX, robotY) = currentRobotsAndPositions[i]
        (dx, dy) = __getUpOrDown(robotX, robotY, maxDist1Sec)
        robotX += dx
        robotY += dy
        # print(i)
        # print(dx,dy)
        # print(robotX,robotY)
        newDetections.append((robotX, robotY, 0.75))
        currentRobotsAndPositions[i] = (robotX, robotY)

    map.addDetectedRobotCoords(newDetections, 1)  # 1s


