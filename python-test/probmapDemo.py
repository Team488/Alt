import probmap
import cv2
# object and robot values not necessary here
map = probmap.ProbMap(2000,1000,1,100,100,1000,1000)

def mouseDownCallback(event,x,y,flags,param):
 if event == cv2.EVENT_LBUTTONDBLCLK:
    print("clicked at ", x," ", y)
    map.addCustomObjectDetection(x,y,500,500,.75) # adding as a 75% probability
map.display_maps()
map.createDisplayClickCallbacks(mouseDownCallback)


def loop():
    # get mouse event
    while(True):
        map.disspateOverTime()
        map.display_maps()
        print(map.getHighestGameObject())

        k = cv2.waitKey(100) & 0xff
        if k == ord("q"):
           break
        if k == ord("c"):
            map.clear_maps()
       
loop()

