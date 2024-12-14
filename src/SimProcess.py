import time
import cv2
import logging
import struct
from networktables import NetworkTables
from tools.NtUtils import getPose2dFromBytes
from mapinternals.localFrameProcessor import LocalFrameProcessor
from mapinternals.CentralProcessor import CentralProcessor
from tools.Constants import CameraExtrinsics, CameraIntrinsics,CameraIdOffsets

# Enable logging for debugging
logging.basicConfig(level=logging.DEBUG)

# MJPEG stream URLs
FRUrl = "http://localhost:3000/Robot_FrontRight%20Camera?dummy=param.mjpg"
FLUrl = "http://localhost:3000/Robot_FrontLeft%20Camera?dummy=param.mjpg"
RRUrl = "http://localhost:3000/Robot_RearRight%20Camera?dummy=param.mjpg"
RLUrl = "http://localhost:3000/Robot_RearLeft%20Camera?dummy=param.mjpg"

# Open the video streams

capFR = cv2.VideoCapture(FRUrl, cv2.CAP_FFMPEG)
capFL = cv2.VideoCapture(FLUrl, cv2.CAP_FFMPEG)
capRR = cv2.VideoCapture(RRUrl, cv2.CAP_FFMPEG)
capRL = cv2.VideoCapture(RLUrl, cv2.CAP_FFMPEG)
caps = [capFR,capFL,capRR,capRL]
# caps = [capFR]
extrinsics = [CameraExtrinsics.FRONTRIGHT,CameraExtrinsics.FRONTLEFT,CameraExtrinsics.REARRIGHT,CameraExtrinsics.REARLEFT]
offsets = [CameraIdOffsets.FRONTRIGHT,CameraIdOffsets.FRONTLEFT,CameraIdOffsets.REARRIGHT,CameraIdOffsets.REARLEFT]
central = CentralProcessor.instance()

if not capFR.isOpened() or not capFL.isOpened() or not capRR.isOpened() or not capRL.isOpened():
    logging.error(f"Failed to open streams! FR:{capFR.isOpened()}, FL:{capFL.isOpened()}, "
                 f"RR:{capRR.isOpened()}, RL:{capRL.isOpened()}")
    exit(1)

# Initialize the frame processor
frameProcessor = LocalFrameProcessor(
    cameraIntrinsics=CameraIntrinsics.SIMULATIONCOLOR,
    cameraExtrinsics=CameraExtrinsics.FRONTRIGHT,
    useRknn=False
)

# Initialize NetworkTables
NetworkTables.initialize(server='127.0.0.1')
postable = NetworkTables.getTable("AdvantageKit/RealOutputs/Vision/AprilTags/Results")
table = NetworkTables.getTable("AdvantageKit/RealOutputs/Odometry")

# Window setup for displaying the camera feed
title = "MJPEG Stream - Front Right Camera"
cv2.namedWindow(title)
cv2.createTrackbar("Camera to inference", title, 1, 4, lambda x: None)
cv2.createTrackbar("Scale Factor", title, 1, 1000, lambda x: None)
cv2.setTrackbarPos("Scale Factor", title, 100)

try:
    while True:
        # Fetch NetworkTables data
        raw_data = postable.getEntry("Estimated Pose").get()
        if raw_data:
            x, y, rotation = getPose2dFromBytes(raw_data)
            logging.info(f"Pose: x={x}, y={y}, rotation={rotation}")
            index = cv2.getTrackbarPos("Camera to inference", title)%4
            cap = caps[index]
            start_time = time.time()
            # Skip older frames in the buffer
            while cap.grab():
                if time.time() - start_time > 0.100:  # Timeout after 100ms
                    logging.warning("Skipping buffer due to timeout.")
                    break
            # Read a frame from the Front-Right camera stream
            ret, frame = cap.read()
            if not ret:
                logging.warning("Failed to retrieve a frame from stream.")
                exit(1)
            
            results = []
            # Process the frame
            res = frameProcessor.processFrame(
                frame,
                robotPosXIn=x * 100,  # Convert meters to cm
                robotPosYIn=y * 100,
                robotYawRad=rotation,
                drawBoxes=True,
                customCameraExtrinsics=extrinsics[index],
                maxDetections=1
            )
        
            results.append((res,offsets[index]))
            
            cv2.imshow(offsets[index].name, frame)
            
            central.processFrameUpdate(results,0.15)
            x,y,p = central.map.getHighestRobot()
            # Update NetworkTables if processing results are available
            scaleFactor = 100# + cv2.getTrackbarPos("Scale factor", title)
            table.getEntry("NoteEstimate3").setDoubleArray([
                x / scaleFactor,
                y / scaleFactor,
                0,
                0
            ])
            logging.debug("Updated NoteEstimate3 entry in NetworkTables.")

            # Display the current frame
            cv2.imshow("aa", central.map.getRobotHeatMap())

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break

finally:
    # Release all resources
    capFR.release()
    capFL.release()
    capRR.release()
    capRL.release()
    cv2.destroyAllWindows()
    logging.info("Released all resources and closed windows.")
