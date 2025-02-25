from mapinternals.KalmanCache import KalmanCache
from mapinternals.UKF import Ukf
from mapinternals.KalmanLabeler import KalmanLabeler
from tools.Constants import CameraIdOffsets


def test_lablerReassignment() -> None:
    cache = KalmanCache()
    ukf = Ukf()
    labler = KalmanLabeler(cache, cache)

    wantedId = 12
    # start by putting an old detection into the cache with some sort of state
    ukf.baseUKF.x = [100, 100, 10, 10]  # 100,100 with velX 10 velY 10
    cache.saveKalmanData(wantedId, ukf)

    # now lets test on a fake detection
    detections = [[8, (110, 110, 2), 0.8, True]]  # id - x,y,z - conf - isRobot

    # the goal is for the labler to replace id 8 with our wanted id (12) this is to simulate a redetection

    labler.updateRealIds(
        detections, CameraIdOffsets.DEPTHLEFT, 1
    )  # id offset does not matter for this

    assert detections[0][0] == wantedId
