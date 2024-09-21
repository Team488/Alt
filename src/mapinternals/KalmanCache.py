import numpy as np
from mapinternals.UKF import Ukf
from tools.Constants import KalmanConstants
"""
    Goals for this class

    This class should handle all the caching of data for each object whether it be robot or gameobject. Each of these will be wrapped in a class that contains a unique label to identify it.
    The cache will store the data with the labels as the key.

    Data stored: All internal kalman filter data for that detection, Previous coordinates and velocity for the detection

    Methods will be simple, just updating what is stored here, and also getting the data as various classes will need it for different reasons.
    The most important is that as the kalman filter is a recursive algorithm it needs previous information it calculated. However since there are many different robots/game objects, each needs their own
    previous information. That is the large reason why this class exists
"""
class KalmanCache:
    def __init__(self) -> None:
        self.savedKalmanData = {}

    
    def saveKalmanData(self,id : int,ukf : Ukf):
        self.savedKalmanData[id] = {
            'x': ukf.baseUKF.x.copy(),  # state vector
            'P': ukf.baseUKF.P.copy(),  # covariance matrix
            # 'Q': ukf.baseUKF.Q.copy(),  # process noise
            # 'R': ukf.baseUKF.R.copy(),  # measurement noise
            # 'K': ukf.baseUKF.K.copy()   # Kalman gain (optional)

        }
    
    def __getSavedKalmanData(self,id : int) -> dict:
        kalmanData = self.savedKalmanData.get(id,None)
        return kalmanData
    
    """ Tries to get stored kalman data. If id is not found will create new kalman data with the x,y provided and an estimated velocity of zero"""
    def getAndLoadKalmanData(self,id : int,x : int,y : int,ukf : Ukf):
        kalmanData = self.__getSavedKalmanData(id)
        if kalmanData is None:
            print(f"Id:{id} is getting new kalman data")
            ukf.baseUKF.x = np.array([x, y, 0, 0]) # todo maybe add an estimated velocity here
            ukf.baseUKF.P = np.eye(4)
            ukf.baseUKF.Q = KalmanConstants.Q
            ukf.baseUKF.R = KalmanConstants.R
        else:
            ukf.baseUKF.x = kalmanData.get('x')
            ukf.baseUKF.P = kalmanData.get('P')
            # ukf.baseUKF.Q = kalmanData.get('Q') # dont really need to save these if they are constant
            # ukf.baseUKF.R = kalmanData.get('R') 
            # ukf.baseUKF.K = kalmanData.get('K') # dont need this most likely
            

