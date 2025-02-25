import cv2
from mapinternals.probmap import ProbMap


def test_getHighest() -> None:
    map = ProbMap()
    testX, testY = (100, 100)
    testProb = 1
    map.addDetectedGameObject(testX, testY, testProb)
    (x, y, prob) = map.getHighestGameObject()
    assert prob >= 0.5
    assert abs(x - testX) < 6  # can vary because of gaussian blob shape
    assert abs(y - testY) < 6


def test_getSpecificValue() -> None:
    map = ProbMap()
    testX, testY = (100, 100)
    testProb = 1
    map.addCustomObjectDetection(testX, testY, 100, 100, testProb)
    specificVal = map.getSpecificGameObjectValue(testX, testY)
    print(map.getHighestGameObject())
    assert specificVal > 0  # todo why is it not the peak of the detection (testX,testY)


def test_prob_max() -> None:
    map = ProbMap()
    testX, testY = (100, 100)
    testProb = 1
    for _ in range(5):
        map.addDetectedGameObject(testX, testY, testProb)
    assert map.getHighestGameObject()[2] <= 1


def test_AddingOutOfBounds() -> None:
    map = ProbMap()
    map.addDetectedGameObject(-20, -20, 1)
    map.addDetectedGameObject(-2000, -2000, 1)

    map.addDetectedGameObject(0, -2000, 1)
    map.addDetectedGameObject(-2000, 0, 1)

    map.addDetectedGameObject(10000, -2000, 1)
    map.addDetectedGameObject(-2000, 10000, 1)

    map.addDetectedGameObject(map.width + 5, map.height + 5, 1)
    map.addDetectedGameObject(10000, 10000, 1)

    map.addDetectedRobot(-20, -20, 1)
    map.addDetectedRobot(-2000, -2000, 1)

    map.addDetectedRobot(0, -2000, 1)
    map.addDetectedRobot(-2000, 0, 1)

    map.addDetectedRobot(10000, -2000, 1)
    map.addDetectedRobot(-2000, 10000, 1)

    map.addDetectedRobot(map.width + 5, map.height + 5, 1)
    map.addDetectedRobot(10000, 10000, 1)
