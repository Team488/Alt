import math
import cv2
import numpy as np
from tools.Constants import CameraIntrinsics,CameraExtrinsics
from mapDemos.utils import drawRobotWithCam

def startDemo():
    size_x = 1000
    size_y = 500

    reef_center = (size_x//3,size_y//2)
    reef_radius = size_x//20

    robot_pos = (0,0)
    robot_width = size_x//25
    robot_height = size_x//25

    robotcam_offset = (robot_width//2,robot_height//2)
    robotcam_yaw_rad = math.pi/2
    robotcam_fov_rad = math.radians(70)


    title = "reef_point_demo"
    rot_trackbar_name = "robot rot deg"
    cv2.namedWindow(title)
    cv2.createTrackbar(rot_trackbar_name,title,0,360, lambda x : None)
    
    def hover_callback(event, x, y, flags, param):
        nonlocal robot_pos
        robot_pos = (x,y)

    cv2.setMouseCallback(title,hover_callback)

    def wrap(ang):
        cut = ang % (2 * math.pi)
        if cut > math.pi:
            # wrap as negative
            return (2*math.pi)-cut
        return cut

    def calculateSeenPoint(frame,reef_pos,reef_radius,robot_pos,robot_rot_rad,robotcam_offset,robotcam_yaw_rad,robotcam_fov_rad):
        dx = robotcam_offset[0]
        dy = robotcam_offset[1]
        cameraPos = (robot_pos[0] + dx*math.cos(robot_rot_rad)-dy*math.sin(robot_rot_rad), robot_pos[1] + dx*math.sin(robot_rot_rad) + dy*math.cos(robot_rot_rad))
        obj_vec = np.subtract(reef_pos,cameraPos)
        
        obj_ang = np.arctan2(obj_vec[1],obj_vec[0])
        cam_ang = robot_rot_rad + robotcam_yaw_rad

        D_ang = (obj_ang-cam_ang)
        cv2.putText(frame,f"Delta {D_ang:.2f} Thresh {robotcam_fov_rad/2:.2f}",(10,20),1,1,(255,255,255),1)

        if wrap(D_ang) > robotcam_fov_rad/2:
            # out of view
            return None

        sixty = math.radians(60)
        
        return round((obj_ang + math.pi)/(sixty))*(sixty), obj_ang+math.pi  # angle of point on reef

    while True:
        frame = np.zeros((size_y,size_x,3),dtype=np.uint8)

        # draw reef
        cv2.circle(frame,reef_center,reef_radius,(100,100,100),1)

        robot_rot = math.radians(cv2.getTrackbarPos(rot_trackbar_name,title))

        drawRobotWithCam(frame,robot_width,robot_height,robot_pos[0],robot_pos[1],robot_rot,robotcam_offset[0],robotcam_offset[1],robotcam_yaw_rad,robotcam_fov_rad,cameraLineLength=500)
        
        res = calculateSeenPoint(frame,reef_center,reef_radius,robot_pos,robot_rot,robotcam_offset,robotcam_yaw_rad,robotcam_fov_rad)
        if res is not None:
            postAng, fullAng = res
            # draw two "posts"
            offset = math.radians(10)
            Vx1 = reef_center[0] + reef_radius * math.cos(postAng-offset)
            Vy1 = reef_center[1] + reef_radius * math.sin(postAng-offset)
            cv2.circle(frame,(int(Vx1),int(Vy1)),5,(255, 192, 203),1)
            Vx2 = reef_center[0] + reef_radius * math.cos(postAng+offset)
            Vy2 = reef_center[1] + reef_radius * math.sin(postAng+offset)
            cv2.circle(frame,(int(Vx2),int(Vy2)),5,(255, 192, 203),1)

            x = reef_center[0] + reef_radius * math.cos(fullAng)
            y = reef_center[1] + reef_radius * math.sin(fullAng)
            # draw actual angle seen
            cv2.circle(frame,(int(x),int(y)),5,(0,0,255),1)


        
        cv2.imshow(title,frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
