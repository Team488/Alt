import cv2
from mapinternals.probmap import ProbMap
import math
from ultralytics import YOLO  # Load the YOLOv8 model

model = YOLO("..\\python\\best.pt")  # Open the model
mapW = 1000
mapH = 800
mapRes = 1
map = ProbMap(mapW,mapH,mapRes,100,100,100,100) 

VRES = 480
HRES = 640
MIDH =  int(HRES/2)
# note 10 inch inside diameter 14 inch outside diameter
NOTEKNOWNSIZE = 13.9 #inches

FX = 896.4286516632743 # focal length along the horizontal azis
HFOVDEG = 70

HFOVRAD = math.radians(HFOVDEG)

# Convert FOV from radians to degrees
#Returns whatever unit NOTEKNOWNSIZE is in || currently inches
def calculateDistance(knownSize, currentSizePixels, focalLength):
    return knownSize * focalLength / currentSizePixels

# calculates angle change per pixel, and multiplies by number of pixels off you are
def calcDefOff(fov, res, pixelDiff):
    fovperPixel = fov / res
    return pixelDiff * fovperPixel

rList = ["Robot","Note"]
cap = cv2.VideoCapture(0)  # path to your video

while cap.isOpened():
    # Read a frame from the video
    print("Reading")
    success, frame = cap.read()

    fps = cap.get(cv2.CAP_PROP_FPS)

    if success:
        # Run YOLOv8 tracking on the frame
        results = model.predict(
            frame, show_boxes=True, conf=0.8, show=False
        )  # images is a list of PIL images
        if results != None and results[0] != None:
            boxes = results[0].boxes.xywh.cpu()
            confs = results[0].boxes.conf.cpu()
            ids = results[0].boxes.cls.cpu()
            # id 0 == robot 1 == note
            for box, conf,id in zip(boxes, confs,ids):
                x, y, w, h = box
                midW = int(w/2)
                midH = int(h/2)
                topX = int(x-midW)
                topY = int(y-midH)
                botX = int(x+midW)
                botY = int(y+midH)
                cv2.rectangle(
                    img=frame,
                    pt1=(topX,topY),
                    pt2=(botX,botY),
                    color=(0, 255, 0),
                    thickness=2,
                )

                distance = calculateDistance(NOTEKNOWNSIZE,int(w),FX)
                bearing = calcDefOff(HFOVRAD,HRES,int(x)-MIDH)
                camY = -math.sin(bearing) * distance
                camX = math.cos(bearing) * distance
                
                map.addDetectedGameObject(int(mapW/2+camX),int(mapH/2+camY),float(conf),1)
                cv2.putText(frame,rList[int(id)],(int(x),int(y)),1,2,(0,255,0))
                
        cv2.imshow("heatmap",map.getHeatMaps()[0])
        # cv2.imshow("Frame",frame)
        # Display the annotated frame
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    
cap.release()
cv2.destroyAllWindows()
