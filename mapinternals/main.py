from pathplanning import CalculateBestPath,LockOnTarget
from coreinterface import CoreInput,CoreOutput
from . import UKF, DetectionType,KalmanCache,KalmanLabeler,MapDetection,probmap

# sample constructor
mapWrapper = probmap(2000,1000,1,100,100,1000,1000)

""" Note! Current methods are not implemented, this is just a skeleton of what it will be like """

def addNewDetection(detectionC : tuple[int,int],detectionType: DetectionType,detectionProb : float):
    # first label detection
    mapDetection : MapDetection = KalmanLabeler.createDetection(detectionC,detectionType,detectionProb) # here we would get the label in a fully boxed class MapDetection

    # next we need to retrieve the stored kalman data for this label

    kalmanData = KalmanCache.getData(mapDetection.detectionLabel) # example method

    # then we pass the new detection through the kalman filter, along with the previous data

    (newPred,newKalmanData) = UKF.passThroughFiter(mapDetection,kalmanData) # example method

    
    # now you can save all this new data however needed
    (px,py,vx,vy,etc) = newPred
    
    KalmanCache.putNewInfo(newPred,newKalmanData) # cache all new data

    # add detection to probmap aswell
    if(DetectionType.isTypeRobot(detectionType)):
        mapWrapper.addDetectedRobot(px,py)
    else:
        mapWrapper.addDetectedGameObject(px,py)

