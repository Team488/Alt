from inference.rknnInferencer import rknnInferencer
import cv2
import time
inf = rknnInferencer("assets/bestV5.rknn")

cap = cv2.VideoCapture("assets/video12qual25clipped.mp4")
while True:
    ret, frame = cap.read()
    if not ret:
        break

    start = time.time()
    results = inf.getResults(frame)
    if results is not None:
        for box,confidence,class_id in results:
            (x1,y1, x2,y2) = box 
            cv2.rectangle(frame, (x1,y1), (x2,y2), (0,255,0),2)
    end = time.time()
    print("Inferencing time fps:",str(1/(end-start)))
    cv2.imshow("frame", frame)

    cv2.waitKey(1)









