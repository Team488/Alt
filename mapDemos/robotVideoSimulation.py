import numpy as np
from ultralytics import YOLO
from mapinternals.probmap import ProbMap
from tools.CsvParser import CsvParser
from tools.Constants import CameraIntrinsics, CameraExtrinsics
from tools.positionEstimator import PositionEstimator
from tools.positionTranslations import CameraToRobotTranslator
import cv2
import math

fieldWidth = 1653 # 54' 3" to cm
fieldHeight = 800 # 26' 3" to cm
res = 5 # cm
robotWidth = 75 # cm
robotHeight = 75 # cm assuming square robot with max frame perimiter of 300
gameObjectWidth = 35 # cm
gameObjectHeight = 35 # cm circular note
simMap = ProbMap(fieldWidth,fieldHeight,res,gameObjectX=gameObjectWidth,gameObjectY=gameObjectHeight,robotX=robotWidth,robotY=robotHeight)

parser = CsvParser("assets/qual25.csv",.1,
                   ("/RealOutputs/PoseSubsystem/RobotPose/rotation/value",
                    "/RealOutputs/PoseSubsystem/RobotPose/translation/x",
                    "/RealOutputs/PoseSubsystem/RobotPose/translation/y"))
parser.removeZeroEntriesAtStart()
csvTimeOffset = 99.8 # time offset to align video start with log movements (seconds)

def startDemo():
    cameraExtr = CameraExtrinsics.DEPTHLEFT
    cameraIntr = CameraIntrinsics.OAKDLITE
    cap = cv2.VideoCapture("assets/video12qual25clipped.mp4")
    firstRun = True
    cap_out = None
    model = YOLO("..\\..\\Braindance\\bestV8.pt")  # Open the model
    estimator = PositionEstimator()
    translator = CameraToRobotTranslator()
    fps = cap.get(cv2.CAP_PROP_FPS)
    timePassed = 0
    timePerFrame = 1/fps 

    while cap.isOpened():
        ret,frame = cap.read()
        if firstRun:
            firstRun = False
            cap_out = cv2.VideoWriter("out.mp4", cv2.VideoWriter_fourcc(*'MP4V'), fps,
                          (frame.shape[1], frame.shape[0]))
        if ret:
            # read and draw robot location
            values = parser.getNearestValues(timePassed + csvTimeOffset)
            rotationRad = float(values[0][1][1])
            positionX = int(float(values[1][1][1]) *100) # m -> cm
            positionY = int(float(values[2][1][1]) *100) # m -> cm
            # print(f"Rotation:{rotationRad} X:{positionX} Y:{positionY}")
            
            if(positionX > fieldWidth):
                print("Error X too large! clipping")    
                positionX = fieldWidth

            if(positionX < 0):
                print("Error X too small! clipping")
                positionX = 0
            
            if(positionY > fieldHeight):
                print("Error y too large! clipping")
                positionY = fieldHeight
            
            if(positionY < 0):
                print("Error y too small! clipping")
                positionY = 0
            
            # flip position y as frc y dir is flipped
            positionY = fieldHeight-positionY
            
            # Run YOLOv8 on the frame
            results = model.predict(
                frame, show_boxes=True, conf=0.8, show=False
            )  # images is a list of PIL images
            
            if results != None and results[0] != None:
                (RelGameObj,RelRobots) = estimator.estimateDetectionPositions(frame,results,cameraIntr)
                if RelGameObj is not None:
                    for gameObj in RelGameObj:
                        ((relCamX,relCamY),conf) = gameObj
                        (relToRobotX,relToRobotY,relToRobotZ) = translator.turnCameraCoordinatesIntoRobotCoordinates(relCamX,relCamY,cameraExtr)
                        simMap.addCustomObjectDetection(positionX + int(relToRobotX),positionY - int(relToRobotY),150,150,conf,timePerFrame)
                
                if RelRobots is not None:
                    for robot in RelRobots:
                        ((relCamX,relCamY,isBlue),conf) = robot
                        (relToRobotX,relToRobotY,relToRobotZ) = translator.turnCameraCoordinatesIntoRobotCoordinates(relCamX,relCamY,cameraExtr)
                        simMap.addCustomRobotDetection(positionX + int(relToRobotX),positionY - int(relToRobotY),250,250,conf,timePerFrame)
                        # simMap.addDetectedRobot(int(relToRobotX),int(relToRobotY),conf,timePerFrame)
            
            (gameObjMap,robotMap) = simMap.getHeatMaps()
            height, width = robotMap.shape
            zeros = np.zeros((height, width), dtype=np.uint8)
            mapView = cv2.merge((zeros,gameObjMap,robotMap))
            __drawRobot(mapView,robotWidth,robotHeight,positionX,positionY,-rotationRad,cameraIntr,cameraExtr)
            frame = __embed_frame(frame,mapView,scale_factor=1/2.7)
            cap_out.write(frame)
            cv2.imshow("view",frame)
            if cv2.waitKey(1) & 0xff == ord('q'):
                return
            simMap.disspateOverTime(timePerFrame)
            
            timePassed+=timePerFrame
        else:
            break

        
        
        
def __drawRobot(frame,width,height,posX,posY,rotation,cameraIntrinsics : CameraIntrinsics, cameraExtrinsic : CameraExtrinsics): # fov 90 deg  | fovLen = 70cm # camera is facing 45 to the left
    # drawing robot
    FrameOffset = math.atan((height/2)/(width/2))
    RobotAngLeft = rotation - FrameOffset
    RobotAngRight = rotation + FrameOffset
    FLx = int(posX + math.cos(RobotAngLeft)*width) 
    FLy = int(posY + math.sin(RobotAngLeft)*height)
    FRx = int(posX + math.cos(RobotAngRight)*width)
    FRy = int(posY + math.sin(RobotAngRight)*height)

    BLx = int(posX - math.cos(RobotAngRight)*width)
    BLy = int(posY - math.sin(RobotAngRight)*height)
    BRx = int(posX - math.cos(RobotAngLeft)*width)
    BRy = int(posY - math.sin(RobotAngLeft)*height)
    cv2.line(frame,(FLx,FLy),(FRx,FRy),(0,0,255),1)
    cv2.line(frame,(BLx,BLy),(BRx,BRy),(255,0,0),1)
    cv2.line(frame,(BLx,BLy),(FLx,FLy),(255,255,255),1)
    cv2.line(frame,(BRx,BRy),(FRx,FRy),(255,255,255),1)

    camX = posX + cameraExtrinsic.getOffsetX()
    camY = posY + cameraExtrinsic.getOffsetY()
    # drawing fov (from center of robot for now) 
    cameraOffset = cameraExtrinsic.getYawOffsetAsRadians()
    fov = cameraIntrinsics.getHFov()
    fovLen = 300 # todo*
    rotLeft = (rotation-cameraOffset)-fov/2
    rotRight = (rotation-cameraOffset)+fov/2

    LeftX = int(camX + math.cos(rotLeft)*fovLen)
    LeftY = int(camY + math.sin(rotLeft)*fovLen)

    RightX = int(camX + math.cos(rotRight)*fovLen)
    RightY = int(camY + math.sin(rotRight)*fovLen)

    camX = int(camX)
    camY = int(camY)

    cv2.line(frame,(camX,camY),(LeftX,LeftY),(255,130,0),1)
    cv2.line(frame,(camX,camY),(RightX,RightY),(255,130,0),1)
    # cv2.line(frame,(RightX,RightY),(LeftX,LeftY),(255,130,0),1)
    



def __embed_frame(exterior_frame, interior_frame, scale_factor=1/3):
    # Get dimensions of the exterior frame
    exterior_height, exterior_width, _ = exterior_frame.shape

    # Resize the interior frame to be a third of the exterior frame's height
    new_height = int(exterior_height * scale_factor)
    new_width = int(interior_frame.shape[1] * (new_height / interior_frame.shape[0]))
    resized_interior_frame = cv2.resize(interior_frame, (new_width, new_height))

    # Define the position where the smaller frame will be placed (bottom-right corner)
    y_offset = exterior_height - resized_interior_frame.shape[0]
    x_offset = exterior_width - resized_interior_frame.shape[1]

    # Insert the resized interior frame into the exterior frame
    exterior_frame[y_offset:y_offset+resized_interior_frame.shape[0], 
                    x_offset:x_offset+resized_interior_frame.shape[1]] = resized_interior_frame

    return exterior_frame


