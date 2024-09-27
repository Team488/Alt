from mapinternals.probmap import ProbMap
def test_addDetection():
    map = ProbMap()
    testX,testY = (100,100)
    testProb = .6
    map.addDetectedGameObject(testX,testY,testProb,1)
    (x,y,prob) = map.getHighestGameObject() 
    assert prob == testProb
    assert abs(x-testX) < 2
    assert abs(y-testY) < 2

# def test_getHighest():
