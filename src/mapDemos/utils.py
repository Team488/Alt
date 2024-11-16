import math
import random
from mapinternals.probmap import ProbMap


def __myRandom(random, a, b):
    return a + random * (b - a)


lastRandAng = None


def getRandomMove(
    robotX, robotY, fieldX, fieldY, maxDistancePerMove, safetyOffset=2
) -> tuple[int, int]:
    randDist = random.randint(int(maxDistancePerMove / 2), maxDistancePerMove)
    randAng = __myRandom(random.random(), 0, 2 * math.pi)
    global lastRandAng
    if lastRandAng != None:
        influenceFactor = __myRandom(random.random(), 0.5, 0.7)
        randAng = randAng * influenceFactor + lastRandAng * (1 - influenceFactor)

    lastRandAng = randAng
    randDx = math.cos(randAng) * randDist
    randDy = math.sin(randAng) * randDist
    # handle clipping
    if robotX + randDx > fieldX:
        randDx = fieldX - robotX - safetyOffset
        lastRandAng = math.pi
    if robotX + randDx < 0:
        lastRandAng = 0
        randDx = robotX + safetyOffset
    if robotY + randDy > fieldY:
        lastRandAng = -math.pi / 2
        randDy = fieldY - robotY - safetyOffset
    if robotY + randDy < 0:
        lastRandAng = math.pi / 2
        randDy = robotY + safetyOffset

    return (int(randDx), int(randDy))


def getRealisticMoveVector(
    robotLocation, nextWaypoint, maxDistancePerMove
) -> tuple[int, int]:
    robotX, robotY = robotLocation
    nextWaypointX, nextWayPointY = nextWaypoint
    mvX, mvY = (nextWaypointX - robotX, nextWayPointY - robotY)
    dist = math.sqrt(mvX**2 + mvY**2)
    if dist <= maxDistancePerMove:
        return (mvX, mvY)
    else:
        return (mvX * maxDistancePerMove / dist, mvY * maxDistancePerMove / dist)


def rescaleCoordsDown(x, y, probmap: ProbMap):
    return x // probmap.resolution, y // probmap.resolution


def rescaleCoordsTogetherDown(coords, probmap: ProbMap):
    return coords[0] // probmap.resolution, coords[1] // probmap.resolution


def rescaleCoordsUp(x, y, probmap: ProbMap):
    return x * probmap.resolution, y * probmap.resolution


def rescaleCoordsTogetherUp(coords, probmap: ProbMap):
    return coords[0] * probmap.resolution, coords[1] * probmap.resolution
