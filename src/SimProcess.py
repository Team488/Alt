import json
import cv2
import struct
from networktables import NetworkTables
import logging
import time
from tools.NtUtils import getPose2dFromBytes
from mapinternals.localFrameProcessor import LocalFrameProcessor
from tools.Constants import CameraExtrinsics,CameraIntrinsics

# Enable logging for debugging
logging.basicConfig(level=logging.DEBUG)

FRUrl = "http://localhost:3000/Robot_FrontRight%20Camera?dummy=param.mjpg"
FLUrl = "http://localhost:3000/Robot_FrontLeft%20Camera?dummy=param.mjpg"
RRUrl = "http://localhost:3000/Robot_RearRight%20Camera?dummy=param.mjpg"
RLUrl = "http://localhost:3000/Robot_RearLeft%20Camera?dummy=param.mjpg"

# Open the video streams
capFR = cv2.VideoCapture(FRUrl,cv2.CAP_FFMPEG)
capFL = cv2.VideoCapture(FLUrl,cv2.CAP_FFMPEG)
capRR = cv2.VideoCapture(RRUrl,cv2.CAP_FFMPEG)
capRL = cv2.VideoCapture(RLUrl,cv2.CAP_FFMPEG)

if not capFR.isOpened() or not capFL.isOpened() or not capRR.isOpened() or not capRL.isOpened():
    print("Failed to open all streams!")
    print(f"FR?{capFR.isOpened()} FL?{capFL.isOpened()} RR?{capRR.isOpened()} RL?{capRL.isOpened()}")
    exit()

FRProcessor = LocalFrameProcessor(cameraIntrinsics=CameraIntrinsics.SIMULATIONCOLOR,cameraExtrinsics=CameraExtrinsics.FRONTRIGHT,useRknn=False)
FLProcessor = LocalFrameProcessor(cameraIntrinsics=CameraIntrinsics.SIMULATIONCOLOR,cameraExtrinsics=CameraExtrinsics.FRONTLEFT,useRknn=False)
RRProcessor = LocalFrameProcessor(cameraIntrinsics=CameraIntrinsics.SIMULATIONCOLOR,cameraExtrinsics=CameraExtrinsics.REARRIGHT,useRknn=False)
RLProcessor = LocalFrameProcessor(cameraIntrinsics=CameraIntrinsics.SIMULATIONCOLOR,cameraExtrinsics=CameraExtrinsics.REARLEFT,useRknn=False)


# Connect to the NetworkTables server on localhost
NetworkTables.initialize(server='127.0.0.1')

# Access the specific table
table = NetworkTables.getTable("AdvantageKit/RealOutputs/Odometry")

# robotTable = table.getSubTable("Field/Robot")

while True:
    
    print(table.getEntry("RobotPosition").getName())
    raw_data = table.getEntry("RobotPosition").get()
    if raw_data is not None:
        x, y, rotation = getPose2dFromBytes(raw_data)

        # Print the decoded values
        print(f"x: {x}, y: {y}, rotation: {rotation}")
    # Read a frame from the stream
    ret, frameFR = capFR.read()
    ret, frameFL = capFL.read()
    ret, frameRR = capRR.read()
    ret, frameRL = capRL.read()
    FRProcessor.processFrame(frameFR,drawBoxes=True)
    # FLProcessor.processFrame(frameFL,drawBoxes=True)
    # RRProcessor.processFrame(frameRR,drawBoxes=True)
    # RLProcessor.processFrame(frameRL,drawBoxes=True)

    if not ret:
        print("Failed to retrieve frame.")
        break

    # Display the frame
    cv2.imshow("MJPEG Stream - Front Right Camera", frameFR)
    cv2.imshow("MJPEG Stream - Front Left Camera", frameFL)
    cv2.imshow("MJPEG Stream - Rear Right Camera", frameRR)
    cv2.imshow("MJPEG Stream - Rear Left Camera", frameRL)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the streams and close any windows
capFL.release()
capFR.release()
capRR.release()
capRL.release()
cv2.destroyAllWindows()
