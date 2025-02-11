import time
import cv2
from inference.MultiInferencer import MultiInferencer
from tools.Constants import InferenceMode
m = MultiInferencer(InferenceMode.ONNXSMALL2025)

cap = cv2.VideoCapture("http://localhost:3000/Robot_FrontRight%20Camera?dummy=param.mjpg")
while cap.isOpened():
    start_time = time.time()
    while cap.grab():
        if time.time() - start_time > 0.100:  # Timeout after 100ms
            break

    ret,frame = cap.read()
    if not ret:
        break
    
    m.run(frame, minConf=0.7, drawBoxes=True)
    cv2.imshow("Frame", frame)

    if cv2.waitKey(100) & 0xFF == ord("q"):
        break        

