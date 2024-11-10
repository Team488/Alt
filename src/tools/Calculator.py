import math
import numpy as np
from tools.Constants import MapConstants


def getDistance(detectionX, detectionY, oldX, oldY, velX, velY, timeStepSeconds):
    newPositionX = oldX + velX * timeStepSeconds
    newPositionY = oldY + velY * timeStepSeconds
    dx = detectionX - newPositionX
    dy = detectionY - newPositionY
    dist = np.linalg.norm([dx, dy])  # euclidian
    return dist


def calculateMaxRange(vx, vy, timeStep, isRobot):
    velocityComponent = np.linalg.norm([vx * timeStep, vy * timeStep])
    if not isRobot:
        return velocityComponent
    # only considering acceleration if its a robot
    maxAcceler = MapConstants.RobotAcceleration.value
    accelerationComponent = (maxAcceler * timeStep * timeStep) / 2
    return velocityComponent + accelerationComponent


def cosineDistance(vec1, vec2):
    # Calculate the dot product
    dot_product = np.dot(vec1, vec2)

    # Calculate the magnitudes (norms)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)

    # Calculate cosine similarity
    return dot_product / (norm_vec1 * norm_vec2)
