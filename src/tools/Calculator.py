import math


def getDistance(
    detectionX, detectionY, estimateX, estimateY, velX, velY, timeStepSeconds
):
    newPositionX = estimateX + velX * timeStepSeconds
    newPositionY = estimateY + velY * timeStepSeconds
    dx = detectionX - newPositionX
    dy = detectionY - newPositionY
    dist = math.sqrt(dx * dx + dy * dy)  # euclidian
    return dist
