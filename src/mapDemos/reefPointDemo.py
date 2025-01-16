import math
import cv2
import numpy as np
from tools.Constants import CameraIntrinsics,CameraExtrinsics,MapConstants
from mapDemos.utils import drawRobotWithCams
from reefTracking.reefPositioner import ReefPositioner

def startDemo():
    size_x = MapConstants.fieldWidth.getCM()
    size_y = MapConstants.fieldHeight.getCM()
    positioner = ReefPositioner()

    robot_pos = (0,0)
    robot_width = MapConstants.robotWidth.getCM()
    robot_height = MapConstants.robotHeight.getCM()

    b_reef_center = MapConstants.b_reef_center.getCM()
    r_reef_center = MapConstants.r_reef_center.getCM()
    reef_radius = int(MapConstants.reefRadius.getCM())

    robotcam_extr = CameraExtrinsics.FRONTRIGHT
    robotcam_intr = CameraIntrinsics.OV9782COLOR


    title = "reef_point_demo"
    rot_trackbar_name = "robot rot deg"
    cv2.namedWindow(title)
    cv2.createTrackbar(rot_trackbar_name,title,0,360, lambda x : None)
    
    def hover_callback(event, x, y, flags, param):
        nonlocal robot_pos
        robot_pos = (x,y)

    cv2.setMouseCallback(title,hover_callback)
    while True:
        is_blue_focus = robot_pos[0] <= size_x/2 # if we are on left half of field, be in "blue mode" else right mode
        focused_reef_center = b_reef_center if is_blue_focus else r_reef_center
        
        frame = np.zeros((size_y,size_x,3),dtype=np.uint8)

        # draw reefs
        cv2.circle(frame,b_reef_center,reef_radius,(255,0,0),1)
        cv2.circle(frame,r_reef_center,reef_radius,(0,0,255),1)

        robot_rot = math.radians(cv2.getTrackbarPos(rot_trackbar_name,title))

        drawRobotWithCams(frame,robot_width,robot_height,robot_pos[0],robot_pos[1],robot_rot,[(robotcam_extr,robotcam_intr)],cameraLineLength=500)
        
        res = positioner.getPostCoordinatesWconst(is_blue_focus,robot_pos,robot_rot,robotcam_extr,robotcam_intr)
        if res is not None:
            # draw two "posts"
            x,y,postidx = res
            cv2.circle(frame,(int(x),int(y)),5,(0,255,0),-1)
            cv2.putText(frame,f"P Idx: {postidx}",(10,20),1,1,(255,255,255),1)
            
            # draw "posts"
            ang = math.radians(60) * postidx # assuming first post starts at angle 0
            offset = math.radians(10)
            Vx1 = focused_reef_center[0] + reef_radius * math.cos(ang-offset)
            Vy1 = focused_reef_center[1] + reef_radius * math.sin(ang-offset)
            cv2.circle(frame,(int(Vx1),int(Vy1)),5,(255, 192, 203),1)
            Vx2 = focused_reef_center[0] + reef_radius * math.cos(ang+offset)
            Vy2 = focused_reef_center[1] + reef_radius * math.sin(ang+offset)
            cv2.circle(frame,(int(Vx2),int(Vy2)),5,(255, 192, 203),1)


        
        cv2.imshow(title,frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
