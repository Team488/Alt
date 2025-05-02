import numpy as np
from filterpy.kalman import UnscentedKalmanFilter
from filterpy.kalman import MerweScaledSigmaPoints
from Alt.Core.Constants.Field import Field

from ..Constants.Kalman import KalmanConstants


class Ukf:
    def __init__(
        self,
        field : Field,
    ) -> None:

        self.fieldX = field.getWidth()
        self.fieldY = field.getHeight()
        
        # Parameters
        self.dt = KalmanConstants.Dt  # Time step

        # Initial state (wont be used)
        self.Dim = 4 # x, y, vx, vy -> len of 4
        self.x_initial = np.array(
            [0, 0, 0, 0] 
        )  

        # Covariance matrices
        self.P_initial = np.eye(4)
        self.Q = np.eye(4) * 0.01  # Process noise covariance
        self.R = np.eye(2) * 0.01  # Measurement noise covariance

        # Sigma points TODO parameterize inputs
        self.points = MerweScaledSigmaPoints(
            self.Dim, alpha=0.5, beta=2.0, kappa=3 - self.Dim
        )

        # UKF initialization (dim z = 2 beccause we only measure x, y)
        self.baseUKF = UnscentedKalmanFilter(
            dim_x=4, dim_z=2, fx=self.fx, hx=self.hx, dt=self.dt, points=self.points
        )
        self.baseUKF.x = self.x_initial
        self.baseUKF.P = self.P_initial
        self.baseUKF.Q = self.Q
        self.baseUKF.R = self.R


    # State transition function
    def fx(self, x, dt):
        old_x, old_y, vel_x, vel_y = x
        new_x = old_x + vel_x * dt
        new_y = old_y + vel_y * dt

        return np.array([new_x, new_y, vel_x, vel_y])

    # Define the measurement function
    def hx(self, x):
        return np.array([x[0], x[1]])

    # Example prediction and update steps
    def predict_and_update(self, measurements):
        self.baseUKF.predict()
        # print(f"Predicted state: {self.baseUKF.x}")

        # Example measurement update (assuming perfect measurement for demonstration)
        measurement = np.array(measurements)
        self.baseUKF.update(measurement)
        # print(f"Updated state: {self.baseUKF.x}")
        return self.baseUKF.x

