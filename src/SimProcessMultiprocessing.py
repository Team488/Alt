if __name__ == "__main__":
    import multiprocessing
    multiprocessing.freeze_support()
    import time
    import json
    import cv2
    import logging
    from concurrent.futures import ProcessPoolExecutor
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

    




    names = ["FRONTRIGHT",
            "FRONTLEFT",
            "REARRIGHT",
            "REARLEFT"]

    offsets = [
                CameraIdOffsets.FRONTRIGHT,
                CameraIdOffsets.FRONTLEFT,
                CameraIdOffsets.REARRIGHT,
                CameraIdOffsets.REARLEFT,
            ]

    central = CentralProcessor.instance()

    # Initialize NetworkTables
    NetworkTables.initialize(server="127.0.0.1")
    postable = NetworkTables.getTable("AdvantageKit/RealOutputs/Vision/AprilTags/Results")
    table = NetworkTables.getTable("AdvantageKit/RealOutputs/Odometry")

    # Window setup for displaying the camera feed
    title = "Simulation Window"
    cv2.namedWindow(title)
    cv2.createTrackbar("Scale Factor", title, 0, 200, lambda x: None)
    cv2.setTrackbarPos("Scale Factor", title, 100)
    cv2.createTrackbar("Epsillon", title, 0, 100, lambda x: None)
    cv2.setTrackbarPos("Epsillon", title, 10)

    manager = multiprocessing.Manager()
    updateMap = manager.dict({name: ([], offsets[i], 0) for i, name in enumerate(names)})
    running = manager.Value('b',True)
    def async_frameprocess(imitatedProcIdx,runningFlag,sharedUpdateMap):
        ASYNCLOOPTIMEMS = 100 #ms (onnx inference with 4 different "processors" on one device is slooow)
        NetworkTables.initialize(server="127.0.0.1")
        postable = NetworkTables.getTable("AdvantageKit/RealOutputs/Vision/AprilTags/Results")
        
        names = ["FRONTLEFT",
                "FRONTRIGHT",
                "REARRIGHT",
                "REARLEFT"]

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
        # MJPEG stream URLs
        FRUrl = "http://localhost:3000/Robot_FrontRight%20Camera?dummy=param.mjpg"
        FLUrl = "http://localhost:3000/Robot_FrontLeft%20Camera?dummy=param.mjpg"
        RRUrl = "http://localhost:3000/Robot_RearRight%20Camera?dummy=param.mjpg"
        RLUrl = "http://localhost:3000/Robot_RearLeft%20Camera?dummy=param.mjpg"
        urls = [FRUrl,FLUrl,RRUrl,RLUrl]

        # individual elements
        capurl = urls[imitatedProcIdx]
        imitatedProcName = names[imitatedProcIdx]
        idoffset = offsets[imitatedProcIdx]
        extrinsic = extrinsics[imitatedProcIdx]
        frameProcessor = LocalFrameProcessor(
                            cameraIntrinsics=CameraIntrinsics.SIMULATIONCOLOR,
                            cameraExtrinsics=extrinsic,
                            useRknn=False,
                            setParallel=True,
                            tryOCR=True)
        cap = cv2.VideoCapture(capurl,cv2.CAP_FFMPEG)
        if not cap.isOpened():
            print("Error failed to open capture!")
            return

        try:
            print(f"Entered async loop for{imitatedProcName}")# try:
            while runningFlag.value:
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

                lastidx = sharedUpdateMap[imitatedProcName][2]
                lastidx += 1
                packet = (res,idoffset,lastidx)
                sharedUpdateMap[imitatedProcName] = packet
                etime = time.time()
                dMS = (etime-start_time)*1000
                sleeptime = 1
                if dMS < ASYNCLOOPTIMEMS:
                    sleeptime = (ASYNCLOOPTIMEMS-dMS)
                    logger.debug(f"Sleeping for {sleeptime}s")
                    # time.sleep(sleeptime)
                else:
                    logger.warning(f"Async Loop Overrun! Time elapsed: {dMS}ms | Max loop time: {ASYNCLOOPTIMEMS}ms")
                cv2.waitKey(1)
                time.sleep(sleeptime/1000)
                cv2.imshow(imitatedProcName,frame)
        except Exception as e:
            print(f"Error!{e}")
            logger.fatal(f"Error! {e}")
        finally:
            logger.debug("Exiting async loop")


    MAINLOOPTIMEMS = 100 #ms
    localUpdateMap = {
        "FRONTLEFT": 0,
        "FRONTRIGHT": 0,
        "REARRIGHT": 0,
        "REARLEFT": 0,
    }
    # Executor outside the with block
    try:
        # Launch processes
        with ProcessPoolExecutor(max_workers=4) as executor:
            futures = [
                executor.submit(
                    async_frameprocess,
                    i,
                    running,
                    updateMap,
                )
                for i in range(4)
            ]

            while True:
                print(futures)
                stime = time.time()
                results = []
                for processName in names:
                    localidx = updateMap[processName][2]
                    packet = updateMap[processName]
                    result, packetidx = packet[:2], packet[2]
                    if localidx == packetidx:
                        continue
                    results.append(result)

                # Central processor logic
                central.processFrameUpdate(results, 1)
                logger.debug("Central processor updated.")

                # GUI update
                cv2.imshow("Simulation Window", central.map.getRobotHeatMap())
                if cv2.waitKey(1) & 0xFF == ord("q"):
                    running.value = False
                    break

                # Maintain loop rate
                elapsed = (time.time() - stime) * 1000
                time.sleep(max(0, MAINLOOPTIMEMS - elapsed) / 1000)

    except KeyboardInterrupt:
        logger.info("Shutting down gracefully...")
    except Exception as e:
        logger.fatal(f"Critical error: {e}")
    finally:
        running.value = False
        cv2.destroyAllWindows()