import numpy as np
import cv2
from filterpy.kalman import UnscentedKalmanFilter as UKF
from filterpy.kalman import MerweScaledSigmaPoints

class Ukf:
    """Obstacles are expected to be in x,y format"""

    def __init__(self, Obstacles: list[tuple[tuple[int, int], tuple[int, int]]], fieldX, fieldY):
        self.obstacles = Obstacles
        self.fieldX = fieldX
        self.fieldY = fieldY
        
        # Parameters
        self.dt = .1  # Time step
        
        # Initial state
        self.x_initial = np.array([50, 50, 10, 10])  # Example initial state (position_x, position_y, velocity_x, velocity_y)
        
        # Covariance matrices
        self.P_initial = np.eye(4)
        self.Q = np.eye(4) * 0.01  # Process noise covariance
        self.R = np.eye(2) * 0.01  # Measurement noise covariance
        
        # Sigma points
        self.points = MerweScaledSigmaPoints(4, alpha=0.1, beta=2.0, kappa=0)
        
        # UKF initialization
        self.ukf = UKF(dim_x=4, dim_z=2, fx=self.fx, hx=self.hx, dt=self.dt, points=self.points)
        self.ukf.x = self.x_initial
        self.ukf.P = self.P_initial
        self.ukf.Q = self.Q
        self.ukf.R = self.R

    # State transition function
    def fx(self, x, dt):
        old_x, old_y, vel_x, vel_y = x
        new_x = old_x + vel_x * dt
        new_y = old_y + vel_y * dt
        # Check for obstacle avoidance
        for obstacle in self.obstacles:
            ((topX, topY), (botX, botY)) = obstacle
            # print(obstacle)
            if self.__isWithin(old_x,new_x,topX,botX) and self.__isWithin(old_y,new_y,topY,botY):
                collisionPoint = self.__adjustCollisionToClosestSide(old_x, old_y, new_x, new_y, obstacle)
                if collisionPoint is not None:
                    print(collisionPoint)
                    adjustedX, adjustedY = collisionPoint
                    new_x = adjustedX
                    
                    new_y = adjustedY
                    break
            print("no collision")
            print("Current " + str((new_x,new_y)))

        return np.array([new_x, new_y, vel_x, vel_y])

    def __adjustCollisionToClosestSide(self,oldX, oldY, newX, newY, obstacle) -> tuple[float, float]:
        collisionPoint = None
        ((topX, topY), (botX, botY)) = obstacle
        
        # Get line from points
        m, b = self.__getLine(oldX, oldY, newX, newY)
        # Find the x, y coordinates of the side that it could collide into
        possibleX, possibleY = self.__getPossibleCollisionSides(oldX, oldY, obstacle)
        
        # Plug into line equation to get other point in the line, if we have x, then find y or vice versa
        YforPossibleX = self.__getYvalue(possibleX, m, b)
        XforPossibleY = self.__getXvalue(possibleY, m, b)
        
        # Check if this found point is where we collide
        # Check if this found point is where we collide
        if botY <= YforPossibleX <= topY:
            collisionPoint = (possibleX, YforPossibleX)
        elif botX <= XforPossibleY <= topX:
            collisionPoint = (XforPossibleY, possibleY)
        return collisionPoint

    def __isWithin(self,oldDim,newDim,topDim,bottomDim):
        topMovement = oldDim if oldDim > newDim else newDim
        bottomMovement = oldDim if oldDim < newDim else newDim
        # handle cases where a point is within first
        if(bottomDim <= topMovement <= topDim) or (bottomDim <= bottomMovement <= topDim):
            return True
        # now check if the old dim and new dim cross these sides
        return (topMovement >= topDim and bottomMovement <= bottomDim)
        
    def __getPossibleCollisionSides(self, oldX, oldY, obstacle) -> tuple[int, int]:
        ((topX, topY), (botX, botY)) = obstacle
        possibleX = topX if oldX > topX else botX
        possibleY = topY if oldY > topY else botY
        return possibleX, possibleY

    def __getLine(self, oldX, oldY, newX, newY) -> tuple[float, float]:
        if(oldX == newX):
            return float('inf'),0
        m = (newY - oldY) / (newX - oldX)
        b = newY - m * newX
        return m, b
    
    def __getXvalue(self, y, m, b):
        return (y - b) / m

    def __getYvalue(self, x, m, b):
        return m * x + b

    # Define the measurement function
    def hx(self, x):
        return np.array([x[0], x[1]])

    # Example prediction and update steps
    def predict_and_update(self, measurements):
        self.ukf.predict()
        print(f"Predicted state: {self.ukf.x}")

        # Example measurement update (assuming perfect measurement for demonstration)
        measurement = np.array(measurements)
        self.ukf.update(measurement)
        print(f"Updated state: {self.ukf.x}")

# Example usage:
obstacles = [((100, 100),(50, 50))]
fieldX = 200
fieldY = 200


ukf = Ukf(obstacles, fieldX, fieldY)

# Example prediction and update
measurements = [50, 50]  # Example measurements
ukf.predict_and_update(measurements)
