import numpy as np
import cv2
from filterpy.kalman import UnscentedKalmanFilter as UKF
from filterpy.kalman import MerweScaledSigmaPoints


def __getLine(oldX, oldY, newX, newY) -> tuple[float, float]:
    m = (newY - oldY) / (newX - oldX)
    b = newY - m * newX
    return m, b

def __getXvalue(y, m, b):
    return (y - b) / m

def __getYvalue(x, m, b):
    return m * x + b

def __getPossibleCollisionSides(oldX, oldY, obstacle) -> tuple[int, int]:
    ((topX, topY), (botX, botY)) = obstacle
    possibleX = topX if oldX > topX else botX
    possibleY = topY if oldY > topY else botY
    return possibleX, possibleY

def __isWithin(oldDim,newDim,topDim,bottomDim):
    topMovement = oldDim if oldDim > newDim else newDim
    bottomMovement = oldDim if oldDim < newDim else newDim
    # handle cases where a point is within first
    if(bottomDim <= topMovement <= topDim) or (bottomDim <= bottomMovement <= topDim):
        return True
    # now check if the old dim and new dim cross these sides
    return (topMovement >= topDim and bottomMovement <= bottomDim)

def __adjustCollisionToClosestSide(oldX, oldY, newX, newY, obstacle) -> tuple[float, float]:
    collisionPoint = None
    ((topX, topY), (botX, botY)) = obstacle
    
    # Get line from points
    m, b = __getLine(oldX, oldY, newX, newY)
    print(f"m{m} b{b}") 
    # Find the x, y coordinates of the side that it could collide into
    possibleX, possibleY = __getPossibleCollisionSides(oldX, oldY, obstacle)
    
    # Plug into line equation to get other point in the line, if we have x, then find y or vice versa
    YforPossibleX = __getYvalue(possibleX, m, b)
    XforPossibleY = __getXvalue(possibleY, m, b)
    
    # Check if this found point is where we collide
    if botY <= YforPossibleX <= topY:
        collisionPoint = (possibleX, YforPossibleX)
    elif botX <= XforPossibleY <= topX:
        collisionPoint = (XforPossibleY, possibleY)
    return collisionPoint

def redrawScene(frame,oldX,oldY,newX,newY,obstacles):
    cv2.arrowedLine(frame,(oldX,oldY),(newX,newY),(0,255,0),2)

    # Check for obstacle avoidance
    for obstacle in obstacles:
        ((topX, topY), (botX, botY)) = obstacle
        print(f"oX{oldX} oY{oldY} nX{newX} nY{newY}")
        if __isWithin(oldX,newX,topX,botX) and __isWithin(oldY,newY,topY,botY):
            collisionPoint = __adjustCollisionToClosestSide(oldX, oldY, newX, newY, obstacle)
            if collisionPoint is not None:
                adjustedX, adjustedY = collisionPoint
                cv2.circle(frame,(int(adjustedX),int(adjustedY)),6,(255,0,0),-1)            
                break
            else:
                print("Hit edge")
        else:
            print("no collision")
    for obstacle in obstacles:
        cv2.rectangle(frame,obstacle[0],obstacle[1],(0,0,255),2)
    cv2.imshow("frame",frame)

def getNewFrame(fieldX,fieldY):
    return np.zeros((fieldX,fieldY,3),dtype=np.int8)


        

# Example usage:
obstacles = [((100, 100),(50, 50))]
fieldX = 200
fieldY = 200

frame = getNewFrame(fieldX,fieldY)



lastX1 = 0
lastY1 = 0
lastX2 = int(fieldX/2)
lastY2 = int(fieldY/2)

def updateX1(val):
    frame = getNewFrame(fieldX,fieldY)
    global lastX1
    global lastY1
    global lastY2
    global lastX2
    global obstacles

    lastX1 = val
    redrawScene(frame,lastX1,lastY1,lastX2,lastY2,obstacles)
    
def updateY1(val):
    frame = getNewFrame(fieldX,fieldY)
    global lastX1
    global lastY1
    global lastY2
    global lastX2
    global obstacles

    lastY1 = val
    redrawScene(frame,lastX1,lastY1,lastX2,lastY2,obstacles)


def updateX2(val):
    frame = getNewFrame(fieldX,fieldY)
    global lastX1
    global lastY1
    global lastY2
    global lastX2
    global obstacles

    lastX2 = val
    redrawScene(frame,lastX1,lastY1,lastX2,lastY2,obstacles)


def updateY2(val):
    frame = getNewFrame(fieldX,fieldY)
    global lastX1
    global lastY1
    global lastY2
    global lastX2
    global obstacles

    lastY2 = val
    redrawScene(frame,lastX1,lastY1,lastX2,lastY2,obstacles)




cv2.namedWindow("testWin")
cv2.createTrackbar("X1","testWin",0,fieldX,updateX1)
cv2.createTrackbar("Y1","testWin",0,fieldY,updateY1)
cv2.createTrackbar("X2","testWin",0,fieldX,updateX2)
cv2.createTrackbar("Y2","testWin",0,fieldY,updateY2)


# Example prediction and update
measurements = [60, 60]  # Example measurements
while(True):
    frame = getNewFrame(fieldX,fieldY)
    redrawScene(frame,lastX1,lastY1,lastX2,lastY2,obstacles)
    if cv2.waitKey(1) & 0xff == ord("q"):
        break

