import numpy as np
from filterpy.kalman import UnscentedKalmanFilter as UKF
from filterpy.kalman import MerweScaledSigmaPoints


class xbotUkf:
    """Obstacles are expected to be in x,y format"""

    def __init__(
        self, Obstacles: list[tuple[tuple[int, int], tuple[int, int]]], fieldX, fieldY
    ):
        self.obstacles = Obstacles
        self.fieldX = fieldX
        self.fieldY = fieldY


# state transition function
def fx(x, dt):
    # x = [pos_x, pos_y, vel_x, vel_y]
    pos_x, pos_y, vel_x, vel_y = x
    pos_x += vel_x * dt
    pos_y += vel_y * dt

    # Check for obstacle avoidance
    for obstacle in obstacles:
        obs_x, obs_y = obstacle
        distance = np.sqrt((pos_x - obs_x) ** 2 + (pos_y - obs_y) ** 2)
        if distance < obstacle_threshold:
            # Adjust velocity to avoid obstacle
            angle = np.arctan2(pos_y - obs_y, pos_x - obs_x)
            vel_x = avoid_speed * np.cos(angle)
            vel_y = avoid_speed * np.sin(angle)

    return np.array([pos_x, pos_y, vel_x, vel_y])


# Define the measurement function
def hx(x):
    # Direct measurement of position
    return np.array([x[0], x[1]])


# Parameters
dt = 0.1  # Time step
obstacle_threshold = 1.0  # Distance threshold for obstacle avoidance
avoid_speed = 1.0  # Speed to avoid obstacles

# Initial state
x_initial = np.array([0, 0, 1, 1])

# Covariance matrices
P_initial = np.eye(4)
Q = np.eye(4) * 0.1
R = np.eye(2) * 0.1

# Sigma points
points = MerweScaledSigmaPoints(4, alpha=0.1, beta=2.0, kappa=0)

# UKF initialization
ukf = UKF(dim_x=4, dim_z=2, fx=fx, hx=hx, dt=dt, points=points)
ukf.x = x_initial
ukf.P = P_initial
ukf.Q = Q
ukf.R = R

# Example prediction step
for _ in range(10):
    ukf.predict()
    print(f"Predicted state: {ukf.x}")

    # Example measurement update (assuming perfect measurement for demonstration)
    measurement = np.array([ukf.x[0], ukf.x[1]])
    ukf.update(measurement)
    print(f"Updated state: {ukf.x}")


# Define the state transition function
def fx(x, dt):
    # x = [pos_x, pos_y, vel_x, vel_y]
    pos_x, pos_y, vel_x, vel_y = x
    pos_x += vel_x * dt
    pos_y += vel_y * dt

    # Check for obstacle avoidance
    for obstacle in obstacles:
        obs_x, obs_y = obstacle
        distance = np.sqrt((pos_x - obs_x) ** 2 + (pos_y - obs_y) ** 2)
        if distance < obstacle_threshold:
            # Adjust velocity to avoid obstacle
            angle = np.arctan2(pos_y - obs_y, pos_x - obs_x)
            vel_x = avoid_speed * np.cos(angle)
            vel_y = avoid_speed * np.sin(angle)

    return np.array([pos_x, pos_y, vel_x, vel_y])


# Define the measurement function
def hx(x):
    # Direct measurement of position
    return np.array([x[0], x[1]])


# Parameters
dt = 0.1  # Time step
obstacle_threshold = 1.0  # Distance threshold for obstacle avoidance
avoid_speed = 1.0  # Speed to avoid obstacles
obstacles = [(5, 5), (10, 10)]  # Known obstacle coordinates

# Initial state
x_initial = np.array([0, 0, 1, 1])

# Covariance matrices
P_initial = np.eye(4)
Q = np.eye(4) * 0.1
R = np.eye(2) * 0.1

# Sigma points
points = MerweScaledSigmaPoints(4, alpha=0.1, beta=2.0, kappa=0)

# UKF initialization
ukf = UKF(dim_x=4, dim_z=2, fx=fx, hx=hx, dt=dt, points=points)
ukf.x = x_initial
ukf.P = P_initial
ukf.Q = Q
ukf.R = R

# Example prediction and update steps
for _ in range(10):
    ukf.predict()
    print(f"Predicted state: {ukf.x}")

    # Example measurement update (assuming perfect measurement for demonstration)
    measurement = np.array([ukf.x[0], ukf.x[1]])
    ukf.update(measurement)
    print(f"Updated state: {ukf.x}")
