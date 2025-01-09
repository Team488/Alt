import cv2
from mapinternals.probmap import ProbMap


def test_getHighest():
    map = ProbMap()
    testX, testY = (100, 100)
    testProb = 1
    map.addDetectedGameObject(testX, testY, testProb)
    (x, y, prob) = map.getHighestGameObject()
    assert prob == 0.5
    assert abs(x - testX) < 5  # can vary because of gaussian blob size
    assert abs(y - testY) < 5


def test_getSpecificValue():
    map = ProbMap()
    testX, testY = (100, 100)
    testProb = 1
    map.addCustomObjectDetection(testX, testY, 100, 100, testProb)
    specificVal = map.getSpecificGameObjectValue(testX, testY)
    print(map.getHighestGameObject())
    assert specificVal > 0  # todo why is it not the peak of the detection (testX,testY)


def test_prob_max():
    map = ProbMap()
    testX, testY = (100, 100)
    testProb = 1
    for _ in range(5):
        map.addDetectedGameObject(testX, testY, testProb)
    assert map.getHighestGameObject()[2] <= 1


test_prob_max()
