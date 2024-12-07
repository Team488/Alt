def startDemo():
    import cv2
    import numpy as np
    from mapinternals.multistateUKF import MultistateUkf
    from tools.Constants import MapConstants

    ukfM = MultistateUkf(10)

    # Initialize an OpenCV window
    window_name = "Multistate UKF Demo"
    cv2.namedWindow(window_name)
    frame_width, frame_height = MapConstants.fieldWidth.getCM(), MapConstants.fieldHeight.getCM()
    
    trackbar_name = "Robot Height"
    robotHeight = 25
    def robotHeightCallback(newHeight):
        nonlocal robotHeight
        robotHeight = newHeight
    cv2.createTrackbar(trackbar_name,window_name,robotHeight,100,robotHeightCallback)


    # Placeholder for mouse position
    mouse_position = np.array([frame_width // 2, frame_height // 2])
    last_mouse_position = np.array([frame_width // 2, frame_height // 2])

    # Mouse callback function to update the observation
    def mouse_callback(event, x, y, flags, param):
        nonlocal mouse_position
        if event == cv2.EVENT_MOUSEMOVE:
            mouse_position = np.array([x, y])

    cv2.setMouseCallback(window_name, mouse_callback)
    # Main simulation loop
    while True:    # Create a blank image for visualization
        frame = np.zeros((frame_height, frame_width, 3), dtype=np.uint8)

        frame = cv2.bitwise_or(frame, cv2.merge((ukfM.obstacles,np.zeros((frame_height,frame_width),dtype=np.uint8),np.zeros((frame_height,frame_width),dtype=np.uint8))))


        # Apply constraints (boundaries, obstacles)

        # Update weights based on mouse position as observation
        observationPosition = mouse_position
        observationVelocity = mouse_position-last_mouse_position

        cv2.putText(frame,f"Pos: {observationPosition} Vel: {observationVelocity}",(0,20),0,1,(0,255,0),2)

        ukfM.predict_and_update(observationPosition + np.random.normal(0,0.01,2))




        # Estimate the state as the weighted mean of particles
        state_estimate = ukfM.getMeanEstimate()

        # Draw particles
        for i in range(ukfM.NUMPOINTS):
            idx = i*ukfM.DIM
            x, y = tuple(map(int,ukfM.baseUKF.x[idx:idx+2]))
            print(f"{x=} {y=}")
            cv2.circle(frame, (x, y), 10, (0, 255, 0), -1)  # Green particles
            

        # Draw estimated state
        cv2.circle(frame, (int(state_estimate[0]), int(state_estimate[1])), 5, (0, 0, 255), -1)  # Red estimate

        # Draw the observation point
        cv2.circle(frame, (observationPosition[0], observationPosition[1]), 5, (255, 0, 0), -1)  # Blue observation

        # Display the frame
        cv2.imshow(window_name, frame)

        last_mouse_position = observationPosition

        # Break the loop if 'q' is pressed
        key = cv2.waitKey(10) & 0xFF
        if key == ord('q'):
            break

    cv2.destroyAllWindows()
