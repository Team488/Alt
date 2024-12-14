import math
import numpy as np
import cv2
from filterpy.kalman import UnscentedKalmanFilter
from filterpy.kalman import MerweScaledSigmaPoints
from tools.Constants import MapConstants


class MultistateUkf:
    """Obstacles are expected to be in x,y format"""

    def __init__(
        self,
        numStates,
        fieldX=MapConstants.fieldWidth.value,
        fieldY=MapConstants.fieldHeight.value,
    ):
        # "Constants"
        self.obstacles = np.load("assets/obstacleMap.npy")
        self.NUMSIMULATEDSTATES = numStates
        self.SINGLESTATELEN = 4
        self.STATELEN = self.NUMSIMULATEDSTATES * self.SINGLESTATELEN
        self.MEASUREMENTLEN = 2
        self.fieldX = fieldX
        self.fieldY = fieldY
        self.maxDist = np.linalg.norm((self.fieldX,self.fieldY))
        # Parameters
        self.dt = 0.1  # Time step


        # Covariance matrices
        self.P_initial = np.eye(self.STATELEN)*0.01
        self.Q = np.eye(self.STATELEN) * 1  # Process noise covariance
        self.R = np.eye(self.MEASUREMENTLEN) * 0.02  # Measurement noise covariance

        # Sigma points
        self.points = MerweScaledSigmaPoints(
            self.STATELEN, alpha=10, beta=2.0, kappa=10
        )

        # UKF initialization
        self.baseUKF = UnscentedKalmanFilter(
            dim_x=self.STATELEN, dim_z=self.MEASUREMENTLEN, fx=self.fx, hx=self.hx, dt=self.dt, points=self.points
        )
        # Initial state
        self.set_state(0,0,0,0) # x,y,vx,vy
        self.baseUKF.P = self.P_initial
        self.baseUKF.Q = self.Q
        self.baseUKF.R = self.R

    def cull_outliers(self, robotHeight = 35): # cm
        # Calculate the Mahalanobis distance of each particle
        particles = self.baseUKF.x.reshape(self.NUMSIMULATEDSTATES, self.SINGLESTATELEN)
        
        weights = np.zeros(len(particles))
        for i, particle in enumerate(particles):
            x,y = tuple(map(int,particle[:2]))
            if(x < 0 or x > self.fieldX or y < 0 or y > self.fieldY):
                weights[i] = 0
                continue
            if(self.obstacles[y][x] <= robotHeight):
                weights[i] = 0
                continue

            diff = particle - np.mean(particles, axis=0)
            particle_covariance = self.baseUKF.P[i * self.SINGLESTATELEN : (i + 1) * self.SINGLESTATELEN, i * self.SINGLESTATELEN : (i + 1) * self.SINGLESTATELEN]
            dist = np.sqrt(np.dot(np.dot(diff.T, np.linalg.inv(particle_covariance)), diff))
            normerr = dist/self.maxDist
            weight = np.exp(- (normerr ** 2) / (2 * 1 ** 2))  # Sigma 1, find proper
            weights[i] = weight
        
        # Add slight noise
        weights += np.random.normal(0.01,0.01,len(particles))
        weights = np.maximum(weights, 0.000001) 
        print(weights)

        # Regenerate particles within the distribution (can use resampling)
        self.regenerate_particles(weights/sum(weights))

    def adjust_noise(self, proximity_to_obstacle, large_change_in_motion):
        # Dynamically adjust process and measurement noise based on conditions
        if proximity_to_obstacle:
            self.baseUKF.Q = np.eye(self.STATELEN) * 0.2  # Increase process noise near obstacles
            self.baseUKF.R = np.eye(self.MEASUREMENTLEN) * 0.1  # Increase measurement noise due to uncertainty near obstacles
        elif large_change_in_motion:
            self.baseUKF.Q = np.eye(self.STATELEN) * 0.3  # Increase noise during large changes in motion
            self.baseUKF.R = np.eye(self.MEASUREMENTLEN) * 0.2  # Increase measurement noise for larger changes
        else:
            self.baseUKF.Q = np.eye(self.STATELEN) * 0.05  # Default process noise
            self.baseUKF.R = np.eye(self.MEASUREMENTLEN) * 0.05  # Default measurement noise


    def regenerate_particles(self,weights): 
        # Resample particles from the remaining particles, ensuring they remain within the distribution
        particles = self.baseUKF.x.reshape(self.NUMSIMULATEDSTATES, self.SINGLESTATELEN)
        # Loop over each particle
        resampled_indices = np.random.choice(self.NUMSIMULATEDSTATES, size=self.NUMSIMULATEDSTATES, p=weights)
        resampled_particles = particles[resampled_indices]
        
        # Resample state and covariance
        self.baseUKF.x = resampled_particles.flatten()
        self.baseUKF.P = np.eye(self.STATELEN) * 0.1  # Reset covariance after resampling

    
    def reset_P(self):
        self.baseUKF.P = np.eye(self.STATELEN)
    
    def set_state(self,x,y,vx,vy):
        newState = [x,y,vx,vy] * self.NUMSIMULATEDSTATES
        self.baseUKF.x = newState

    # State transition function
    # State transition function
    def fx(self, x, dt,robotHeight = 35):
        for i in range(self.NUMSIMULATEDSTATES):
            idx = i * self.SINGLESTATELEN  
            old_x, old_y, vel_x, vel_y = x[idx:idx+self.SINGLESTATELEN]
            
            # Independent noise for each particle's velocity (to make them diverge)
            noise_x = np.random.normal(0, 0.000001)  # Add small noise to x velocity
            noise_y = np.random.normal(0, 0.000001)  # Add small noise to y velocity
            
            # New state update with noise
            new_x = old_x + (vel_x) * dt + noise_x
            new_y = old_y + (vel_y) * dt + noise_y
            
            # # Check if the particle is outside the bounds of the field
            # if new_x < 0 or new_x > self.fieldX:
            #     new_x = np.clip(new_x, 0, self.fieldX)  # Clamp to field boundary
            # if new_y < 0 or new_y > self.fieldY:
            #     new_y = np.clip(new_y, 0, self.fieldY)  # Clamp to field boundary

            # fixxx thissss
            # # Check if the particle collides with any obstacles (assuming obstacle map is in the form of a 2D array)
            # # Assuming obstacle height of 35 cm or whatever value you use
            # if int(new_x) < self.fieldX and int(new_y) < self.fieldY:
            #     if self.obstacles[int(new_y), int(new_x)] <= robotHeight:  # Assume 35 cm is the minimum height for no collision
            #         # If it hits an obstacle, we adjust the position or reset it
            #         new_x, new_y = self.handle_obstacle_collision(new_x, new_y)

            # Update the particle's state
            x[idx:idx+self.SINGLESTATELEN] = new_x, new_y, vel_x, vel_y

        return x

    # Handle collision by either resetting position or applying a penalty
    def handle_obstacle_collision(self, x, y):
        # Handle collisions: could reset to a valid point or apply a penalty
        # For example, reset the position to the nearest valid point (outside the obstacle)
        for dx in range(-1, 2):  # Try to move within a small range to avoid obstacles
            for dy in range(-1, 2):
                new_x, new_y = x + dx, y + dy
                if self.is_valid_position(new_x, new_y):
                    return new_x, new_y
        return x, y  # If no valid position is found, return the current position

    # Check if a position is valid (within bounds and not an obstacle)
    def is_valid_position(self, x, y):
        if x < 0 or x > self.fieldX or y < 0 or y > self.fieldY:
            return False  # Outside the bounds
        if self.obstacles[int(y), int(x)] <= 35:  # Assuming the obstacle map defines obstacles
            return False  # Collides with an obstacle
        return True


    def hx(self, x):
        # Calculate the mean position (x, y) across all particles
        mean_x = np.mean([x[i * self.SINGLESTATELEN] for i in range(self.NUMSIMULATEDSTATES)])
        mean_y = np.mean([x[i * self.SINGLESTATELEN + 1] for i in range(self.NUMSIMULATEDSTATES)])
        return np.array([mean_x, mean_y])  # Return the mean as the measurement

    def getMeanEstimate(self):
        return self.hx(self.baseUKF.x)

    def predict_and_update(self, measurements, proximity_to_obstacle=False, large_change_in_motion=False):
        self.adjust_noise(proximity_to_obstacle, large_change_in_motion)  # Adjust noise based on conditions
        
        self.baseUKF.predict()
        
        # Cull outliers and regenerate particles
        self.cull_outliers()  # Use a threshold based on Mahalanobis distance
        
        measurement = np.array(measurements)
        self.baseUKF.update(measurement)
        
        return self.baseUKF.x



