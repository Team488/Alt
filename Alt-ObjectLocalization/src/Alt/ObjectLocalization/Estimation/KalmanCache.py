import numpy as np

from .KalmanEntry import KalmanEntry
from .UKF import Ukf

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

    def getKeySet(self, copy : bool = True) -> set[int]:
        if copy:
            return set(self.savedKalmanData.keys())
        else:
            return self.savedKalmanData.keys()

    def saveKalmanData(self, id: int, ukf: Ukf) -> None:
        self.savedKalmanData[id] = KalmanEntry(ukf.baseUKF.x, ukf.baseUKF.P)

    def removeKalmanEntry(self, id: int) -> None:
        del self.savedKalmanData[id]

    def getSavedKalmanData(self, id: int) -> KalmanEntry:
        kalmanData = self.savedKalmanData.get(id, None)
        return kalmanData

    """ Tries to get stored kalman data. If id is not found will create new kalman data with the x,y provided and an estimated velocity of zero"""

    def LoadInKalmanData(self, id: int, x: int, y: int, ukf: Ukf) -> None:
        kalmanData = self.getSavedKalmanData(id)
        if kalmanData is None:
            print(f"Id:{id} is getting new kalman data")
            ukf.baseUKF.x = np.array(
                [x, y, 0, 0]
            )  # todo maybe add an estimated velocity here
            ukf.baseUKF.P = np.eye(4) * 0.01
        else:
            ukf.baseUKF.x = kalmanData.X
            ukf.baseUKF.P = kalmanData.P
