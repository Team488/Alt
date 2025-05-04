from enum import Enum

import numpy as np

class KalmanConstants:
    Q = np.eye(4) * 0.01  # Process noise covariance
    R = np.eye(2) * 0.01  # Measurement noise covariance
    Dt = 0.05, # baseline 20 fps assumption 


class LabelingConstants(Enum):
    MAXFRAMESNOTSEEN = 60  # around 2-3 sec
