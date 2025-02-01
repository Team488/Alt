import math
import numpy as np

def inverse_transform(T):
    R = T[:3, :3]  # Rotation matrix
    t = T[:3, 3]   # Translation vector

    R_inv = R.T  # Inverse of rotation matrix (R^-1 = R^T for rotation matrices)
    t_inv = -R_inv @ t  # Inverse translation

    T_inv = np.eye(4)
    T_inv[:3, :3] = R_inv
    T_inv[:3, 3] = t_inv

    return T_inv

# (Replace with actual values)
T_robot_to_target = np.array([
    [1, 0, 0, 1.524], 
    [0, 1, 0, 0],
    [0, 0, 1, 0],
    [0, 0, 0, 1]
])
camRot = math.radians(-177.6)
T_camera_to_target = np.array([
    [math.cos(camRot), -math.sin(camRot), 0, 1.175],  
    [math.sin(camRot), math.cos(camRot), 0, 0.34],
    [0, 0, 1, 0],
    [0, 0, 0, 1]
])

# Compute inverse of camera-to-target transform
T_target_to_camera = inverse_transform(T_camera_to_target)

# Compute robot-to-camera transform
T_robot_to_camera = T_robot_to_target @ T_target_to_camera

print("Robot to Camera Transform:\n", T_robot_to_camera)
