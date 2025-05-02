import numpy as np
from Alt.Core.Constants.Field import Field
from Alt.Core.Units.Poses import Transform3d

from Alt.ObjectLocalization.Estimation.KalmanCache import KalmanCache
from Alt.ObjectLocalization.Estimation.UKF import Ukf
from Alt.ObjectLocalization.Estimation.KalmanLabeler import KalmanLabeler
from Alt.ObjectLocalization.Localization.LocalizationResult import LocalizationResult, DeviceLocalizationResult
from Alt.ObjectLocalization.Constants.Kalman import LabelingConstants


def test_lablerReassignment() -> None:
    cache = KalmanCache()
    ukf = Ukf(Field(1000,1000))
    labler = KalmanLabeler([cache], 1)

    wantedId = 12
    # start by putting an old detection into the cache with some sort of state
    ukf.baseUKF.x = [100, 100, 10, 10]  # 100,100 with velX 10 velY 10
    cache.saveKalmanData(wantedId, ukf)

    # now lets test on a fake detection
    fakeId = 8
    result = DeviceLocalizationResult([LocalizationResult(Transform3d(110, 110, 10), 0, 1, fakeId, np.zeros((10,10)))], "testDevice")

    # the goal is for the labler to replace id 8 with our wanted id (12) this is to simulate a redetection
    labler.updateRealIds(result, 1) 
    # since id 12 existed before, and fakeid 8 is new, since the old object is in range of the new one, it will be reassigned the old id
    assert result.localizedResults[0].deepsort_id == wantedId

    # now lets test with one thats out of range
    result = DeviceLocalizationResult([LocalizationResult(Transform3d(120, 120, 10), 0, 1, fakeId, np.zeros((10,10)))], "testDevice")  
    # out of range should stay as fakeId
    labler.updateRealIds(result, 1)
    assert result.localizedResults[0].deepsort_id == fakeId

    # now lets test with multiple to ensure the closer one is preffered (this functionality should change soon)
    result = DeviceLocalizationResult([
        LocalizationResult(Transform3d(105, 105, 10), 0, 1, fakeId, np.zeros((10,10))),
        LocalizationResult(Transform3d(106, 106, 10), 0, 1, fakeId, np.zeros((10,10)))], "testDevice")  

    labler.updateRealIds(result, 1)
    assert result.localizedResults[0].deepsort_id == wantedId
    assert result.localizedResults[1].deepsort_id == fakeId


def test_lablerMaxFramesNotSeen():
    cache = KalmanCache()
    ukf = Ukf(Field(1000,1000))
    labler = KalmanLabeler([cache], 1)

    wantedId = 12
    # start by putting an old detection into the cache with some sort of state
    ukf.baseUKF.x = [100, 100, 10, 10]  # 100,100 with velX 10 velY 10
    cache.saveKalmanData(wantedId, ukf)

    # iterate more than maxFramesNotSeen and see if its removed from the cache
    for _ in range(LabelingConstants.MAXFRAMESNOTSEEN.value):
        labler.updateRealIds(DeviceLocalizationResult([], "testDevice"), 1)

    assert cache.getSavedKalmanData(wantedId) is not None # one more to remove

    labler.updateRealIds(DeviceLocalizationResult([], "testDevice"), 1)

    assert cache.getSavedKalmanData(wantedId) is None
