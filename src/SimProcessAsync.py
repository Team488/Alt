import time
import cv2
import logging
from concurrent.futures import ThreadPoolExecutor
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
                    useRknn=False,setParallel=False
                    ) for i in range(len(offsets))]

central = CentralProcessor.instance()

# Initialize NetworkTables
NetworkTables.initialize(server="127.0.0.1")
postable = NetworkTables.getTable("AdvantageKit/RealOutputs/Vision/AprilTags/Results")
table = NetworkTables.getTable("AdvantageKit/RealOutputs/Odometry")

# Window setup for displaying the camera feed
title = "Simulation Window"
cv2.namedWindow(title)
cv2.createTrackbar("Camera to inference", title, 1, 4, lambda x: None)
cv2.createTrackbar("Scale Factor", title, 1, 1000, lambda x: None)
cv2.setTrackbarPos("Scale Factor", title, 100)

updateMap = {
    "FRONTLEFT": ([], offsets[0], 0),
    "FRONTRIGHT": ([], offsets[1], 0),
    "REARRIGHT": ([], offsets[2], 0),
    "REARLEFT": ([], offsets[3], 0),
}
ASYNCLOOPTIMEMS = 100 #ms (onnx inference with 4 different "processors" on one device is slooow)
def async_frameprocess(imitatedProcIdx):
    cap = caps[imitatedProcIdx]
    imitatedProcName = names[imitatedProcIdx]
    idoffset = offsets[imitatedProcIdx]
    frameProcessor = frameProcessors[imitatedProcIdx]
    
    try:
        while True:
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
            )

            global updateMap
            lastidx = updateMap[imitatedProcName][2]
            lastidx += 1
            packet = (res,idoffset,lastidx)
            updateMap[imitatedProcName] = packet
            etime = time.time()
            dMS = (etime-start_time)*1000
            sleeptime = 0
            if dMS < ASYNCLOOPTIMEMS:
                sleeptime = (ASYNCLOOPTIMEMS-dMS)
                logger.debug(f"Sleeping for {sleeptime}s")
                # time.sleep(sleeptime)
            else:
                logger.warning(f"Async Loop Overrun! Time elapsed: {dMS}ms | Max loop time: {ASYNCLOOPTIMEMS}ms")
            cv2.waitKey(1+sleeptime)
            cv2.imshow(imitatedProcName,frame)
    except Exception as e:
        logger.fatal(f"Error! {e}")

MAINLOOPTIMEMS = 100#ms
localUpdateMap = {
    "FRONTLEFT": 0,
    "FRONTRIGHT": 0,
    "REARRIGHT": 0,
    "REARLEFT": 0,
}
with ThreadPoolExecutor(max_workers=4) as exe:
    exe.submit(async_frameprocess,0)
    exe.submit(async_frameprocess,1)
    exe.submit(async_frameprocess,2)
    exe.submit(async_frameprocess,3)
    try:
        while True:
            stime = time.time()
            results = []
            for processName in names:
                localidx = localUpdateMap[processName]
                packet = updateMap[processName]
                print(f"{packet=}")
                result,packetidx = packet[:2],packet[2]
                if localidx == packetidx:
                    # same data
                    continue
                localUpdateMap[processName] = packetidx
                results.append(result)

            central.processFrameUpdate(results,MAINLOOPTIMEMS/1000)
            x, y, p = central.map.getHighestRobot()
            # Update NetworkTables if processing results are available
            scaleFactor = 100  # + cv2.getTrackbarPos("Scale factor", title)
            table.getEntry("Target Estimate").setDoubleArray(
                [x / scaleFactor, y / scaleFactor, 0, 0]
            )
            logger.debug("Updated Target Estimate entry in NetworkTables.")

            # Display the current frame
            etime = time.time()
            dMS = (etime-stime)*1000
            waittime = 0
            if dMS < MAINLOOPTIMEMS:
                waittime = int(MAINLOOPTIMEMS-dMS)
            else:
                logger.warning(f"Overran Loop! Time elapsed: {dMS}ms | Max loop time: {MAINLOOPTIMEMS}ms")
            cv2.imshow("aa", central.map.getRobotHeatMap())

            # Break the loop if 'q' is pressed
            if cv2.waitKey(1+waittime) & 0xFF == ord("q"):
                break
    except Exception as e:
        logger.fatal(f"Main thread error!: {e}")
    finally:
        # Release all resources
        capFR.release()
        capFL.release()
        capRR.release()
        capRL.release()
        cv2.destroyAllWindows()
        exe.shutdown(wait=False)
        logging.info("Released all resources and closed windows.")
