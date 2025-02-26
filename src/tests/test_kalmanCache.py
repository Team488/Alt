from mapinternals.KalmanCache import KalmanCache
from mapinternals.UKF import Ukf


def test_storing() -> None:
    testCache = KalmanCache()
    testUkf = Ukf()
    testUkf.baseUKF.x = [1, 2, 3, 4]
    testCache.saveKalmanData(10, testUkf)
    # simple test
    assert testCache.getSavedKalmanData(10).X == [1, 2, 3, 4]
    # non contained id == None
    assert testCache.getSavedKalmanData(99) == None

    testUkf.baseUKF.x = [4, 5, 6, 7]

    testCache.saveKalmanData(10, testUkf)
    # should always overwrite
    assert testCache.getSavedKalmanData(10).X == [4, 5, 6, 7]
