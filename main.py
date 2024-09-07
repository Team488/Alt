from mapinternals.probmap import ProbMap
from mapTests import probmapClickDemo

""" Sample method """

# def addNewDetection(detectionC : tuple[int,int],detectionType: DetectionType,detectionProb : float):
#     # first label detection
#     mapDetection : MapDetection = KalmanLabeler.createDetection(detectionC,detectionType,detectionProb) # here we would get the label in a fully boxed class MapDetection

#     # next we need to retrieve the stored kalman data for this label

#     kalmanData = KalmanCache.getData(mapDetection.detectionLabel) # example method

#     # then we pass the new detection through the kalman filter, along with the previous data

#     (newPred,newKalmanData) = UKF.passThroughFiter(mapDetection,kalmanData) # example method

    
#     # now you can save all this new data however needed
#     (px,py,vx,vy,etc) = newPred
    
#     KalmanCache.putNewInfo(newPred,newKalmanData) # cache all new data

#     # add detection to probmap aswell
#     if(DetectionType.isTypeRobot(detectionType)):
#         mapWrapper.addDetectedRobot(px,py)
#     else:
#         mapWrapper.addDetectedGameObject(px,py)

map = ProbMap(2000,1000,1,100,100,100,100)

while(True):
    mapViewGameObject,mapViewRobot = map.getHeatMaps()
    break