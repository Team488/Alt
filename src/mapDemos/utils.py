import math
import random
def __myRandom(random, a, b):
    return a + random * (b - a)

lastRandAng = None
def getRandomMove(
    robotX, robotY, fieldX, fieldY, maxDistancePerMove,safetyOffset = 2
) -> tuple[int, int]:
    randDist = random.randint(int(maxDistancePerMove / 2), maxDistancePerMove)
    randAng = __myRandom(random.random(), 0, 2 * math.pi)
    global lastRandAng
    if(lastRandAng != None):
        influenceFactor = __myRandom(random.random(),.5,.7)
        randAng = randAng*influenceFactor + lastRandAng*(1-influenceFactor) 

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
        lastRandAng = -math.pi/2
        randDy = fieldY - robotY - safetyOffset
    if robotY + randDy < 0:
        lastRandAng = math.pi/2
        randDy = robotY + safetyOffset

    return (int(randDx), int(randDy))
