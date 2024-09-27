import math
import numpy as np
from tools.Constants import MapConstants

def getDistance(
    detectionX, detectionY, oldX, oldY, velX, velY, timeStepSeconds
):
    newPositionX = oldX + velX * timeStepSeconds
    newPositionY = oldY + velY * timeStepSeconds
    dx = detectionX - newPositionX
    dy = detectionY - newPositionY
    dist = np.linalg.norm([dx, dy])  # euclidian
    return dist


def calculateMaxRange(vx,vy,timeStep,isRobot):
    velocityComponent = np.linalg.norm([vx * timeStep, vy * timeStep])
    if not isRobot:
        return velocityComponent
    # only considering acceleration if its a robot
    maxAcceler = MapConstants.RobotAcceleration.value
    accelerationComponent = (maxAcceler*timeStep*timeStep)/2
    return velocityComponent + accelerationComponent
    
    

