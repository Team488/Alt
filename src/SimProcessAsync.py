import struct
import time
import json
import cv2
import logging
from concurrent.futures import ThreadPoolExecutor
import msgpack
from networktables import NetworkTables
from tools.NtUtils import getPose2dFromBytes
from mapinternals.localFrameProcessor import LocalFrameProcessor
from mapinternals.CentralProcessor import CentralProcessor
from tools.Constants import CameraExtrinsics, CameraIntrinsics, CameraIdOffsets

processName = "Simulation_Process"
logger = logging.getLogger(processName)
fh = logging.FileHandler(filename=f"logs/{processName}.log",mode="w")
fh.setLevel(logging.INFO)
ch = logging.StreamHandler()
ch.setLevel(logging.DEBUG)
 # create formatter and add it to the handlers
formatter = logging.Formatter('-->%(asctime)s - %(name)s:%(levelname)s - %(message)s')
fh.setFormatter(formatter)
logger.addHandler(fh)
logger.addHandler(ch)

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

if (
    not capFR.isOpened()
    or not capFL.isOpened()
    or not capRR.isOpened()
    or not capRL.isOpened()
):
    logging.error(
        f"Failed to open streams! FR:{capFR.isOpened()}, FL:{capFL.isOpened()}, "
        f"RR:{capRR.isOpened()}, RL:{capRL.isOpened()}"
    )
    exit(1)

names = ["FRONTLEFT",
        "FRONTRIGHT",
        "REARRIGHT",
        "REARLEFT"]
caps = [capFR, capFL, capRR, capRL]

extrinsics = [
    CameraExtrinsics.FRONTRIGHT,
    CameraExtrinsics.FRONTLEFT,
    CameraExtrinsics.REARRIGHT,
    CameraExtrinsics.REARLEFT,
]
offsets = [
    CameraIdOffsets.FRONTRIGHT,
    CameraIdOffsets.FRONTLEFT,
    CameraIdOffsets.REARRIGHT,
    CameraIdOffsets.REARLEFT,
]

frameProcessors = [LocalFrameProcessor(
                    cameraIntrinsics=CameraIntrinsics.SIMULATIONCOLOR,
                    cameraExtrinsics=extrinsics[i],
                    useRknn=False,setParallel=True,tryOCR=True
                    ) for i in range(len(offsets))]

central = CentralProcessor.instance()

# Initialize NetworkTables
NetworkTables.initialize(server="127.0.0.1")
postable = NetworkTables.getTable("AdvantageKit/RealOutputs/Vision/AprilTags/Results")
table = NetworkTables.getTable("AdvantageKit/RealOutputs/Odometry")

# def pack_pose3d(translation, quaternion, index):     
#     msgpack.packb({
#     "translation": {"x": translation[0], "y": translation[1], "z": translation[2]},
#     "rotation/q": {"w": quaternion[0], "x": quaternion[1], "y": quaternion[2], "z": quaternion[3]}
#     })

#     return keys

# def send_pose3d_array(poses,name):
#     """
#     Send an array of Pose3d to NetworkTables in the AdvantageScope format.
#     :param poses: List of tuples [(translation1, quaternion1), (translation2, quaternion2), ...]
#     """

#     # Create a structure for each Pose3d and push it to NetworkTables
#     for index, (translation, quaternion) in enumerate(poses):
#         pose_data = pack_pose3d(translation, quaternion, index)

#         # Push each individual value to NetworkTables with unique keys for each Pose3d
#         for key, value in pose_data.items():
#             table.putNumber(f"{name}/{index}/{key}", value)

#     table.putNumber(f"{name}/length", len(poses))

# # Example data
# poses = [
#     ((1.0, 2.0, 3.0), (1.0, 0.0, 0.0, 0.0)),  # Pose1: translation, quaternion
#     ((4.0, 5.0, 6.0), (0.707, 0.707, 0.0, 0.0)),  # Pose2: translation, quaternion
# ]

# # Send the Pose3d array
# # Push the byte array to NetworkTables

# while True:
#     send_pose3d_array(poses,":((")
#     time.sleep(0.1)





# exit(0)


# Window setup for displaying the camera feed
title = "Simulation Window"
cv2.namedWindow(title)
cv2.createTrackbar("Scale Factor", title, 0, 200, lambda x: None)
cv2.setTrackbarPos("Scale Factor", title, 100)
cv2.createTrackbar("Epsillon", title, 0, 100, lambda x: None)
cv2.setTrackbarPos("Epsillon", title, 10)

updateMap = {
    "FRONTLEFT": ([], offsets[0], 0),
    "FRONTRIGHT": ([], offsets[1], 0),
    "REARRIGHT": ([], offsets[2], 0),
    "REARLEFT": ([], offsets[3], 0),
}
ASYNCLOOPTIMEMS = 100 #ms (onnx inference with 4 different "processors" on one device is slooow)
def async_frameprocess(imitatedProcIdx):
    global running
    cap = caps[imitatedProcIdx]
    imitatedProcName = names[imitatedProcIdx]
    idoffset = offsets[imitatedProcIdx]
    frameProcessor = frameProcessors[imitatedProcIdx]
    
    try:
        while running:
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
            
            # Fetch NetworkTables data
            pos = (0,0,0)
            raw_data = postable.getEntry("Estimated Pose").get()
            if raw_data:
                pos = getPose2dFromBytes(raw_data)
            else:
                logger.warning("Cannot get robot location from network tables!")
            
            # Process the frame
            res = frameProcessor.processFrame(
                frame,
                robotPosXCm=pos[0] * 100,  # Convert meters to cm
                robotPosYCm=pos[1] * 100,
                robotYawRad=pos[2],
                drawBoxes=True,
                maxDetections=1
            )

            global updateMap
            lastidx = updateMap[imitatedProcName][2]
            lastidx += 1
            packet = (res,idoffset,lastidx)
            updateMap[imitatedProcName] = packet
            etime = time.time()
            dMS = (etime-start_time)*1000
            sleeptime = 0.001
            if dMS < ASYNCLOOPTIMEMS:
                sleeptime = (ASYNCLOOPTIMEMS-dMS)
                logger.debug(f"Sleeping for {sleeptime}s")
                # time.sleep(sleeptime)
            else:
                logger.warning(f"Async Loop Overrun! Time elapsed: {dMS}ms | Max loop time: {ASYNCLOOPTIMEMS}ms")
            cv2.waitKey(1)
            time.sleep(waittime/1000)
            cv2.imshow(imitatedProcName,frame)
        logger.debug("Exiting async loop")
    except Exception as e:
        logger.fatal(f"Error! {e}")
    finally:
        cap.release()

running = True
MAINLOOPTIMEMS = 100 #ms
localUpdateMap = {
    "FRONTLEFT": 0,
    "FRONTRIGHT": 0,
    "REARRIGHT": 0,
    "REARLEFT": 0,
}
# Executor outside the with block
globalexe = ThreadPoolExecutor(max_workers=4)
futures = [globalexe.submit(async_frameprocess, i) for i in range(1)]

try:
    while running:
        stime = time.time()
        results = []
        for processName in names:
            localidx = localUpdateMap[processName]
            packet = updateMap[processName]
            # print(f"{packet=}")
            result, packetidx = packet[:2], packet[2]
            if localidx == packetidx:
                continue
            localUpdateMap[processName] = packetidx
            results.append(result)

        central.processFrameUpdate(results, MAINLOOPTIMEMS/1000)
        x, y, p = central.map.getHighestRobot()
        scaleFactor = 100  # cm to m
        table.getEntry("Target Estimate").setDoubleArray(
            [x / scaleFactor, y / scaleFactor, 0, 0]
        )
        logger.debug("Updated Target Estimate entry in NetworkTables.")

        etime = time.time()
        dMS = (etime - stime) * 1000
        waittime = 0.001
        if dMS < MAINLOOPTIMEMS:
            waittime = int(MAINLOOPTIMEMS - dMS)
        else:
            logger.warning(f"Overran Loop! Time elapsed: {dMS}ms | Max loop time: {MAINLOOPTIMEMS}ms")
        cv2.imshow(title, central.map.getRobotHeatMap())

        # Handle keyboard interrupt with cv2.waitKey()
        if cv2.waitKey(1) & 0xFF == ord("q"):
            running = False

        time.sleep(waittime / 1000)

except KeyboardInterrupt:
    print("Keyboard Interrupt detected, shutting down...")
    running = False

finally:
    # Gracefully shut down threads
    globalexe.shutdown(wait=True)

    # Clean up resources
    cv2.destroyAllWindows()
    if capFL.isOpened(): capFL.release()
    if capFR.isOpened(): capFR.release()
    if capRL.isOpened(): capRL.release()
    if capRR.isOpened(): capRR.release()
    logging.info("Released all resources and closed windows.")