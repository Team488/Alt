import math
import cv2
import numpy as np
from tools.Constants import CameraIntrinsics,CameraExtrinsics
from mapDemos.utils import drawRobot

def startDemo():
    size_x = 1000
    size_y = 500

    reef_center = (size_x//2,size_y//2)
    reef_radius = size_x//20

    robot_pos = (0,0)
    robot_width = size_x//25
    robot_height = size_x//25

    robot_cam_offset = (0,0)
    robot_yaw_offset_rad = 0


    title = "reef_point_demo"

    cv2.namedWindow(title)
    
    def hover_callback(event, x, y, flags, param):
        nonlocal robot_pos
        robot_pos = (x,y)

    cv2.setMouseCallback(title,hover_callback)
    

    def calculateSeenPoint(reef_pos,reef_radius,robot_pos,robot_rot_rad,robot_cam_offset,robot_yaw_offset_rad):
        dx = robot_cam_offset[0]
        dy = robot_cam_offset[1]
        cameraPos = (robot_pos[0] + dx*math.cos(robot_rot_rad)-dy*math.sin(robot_rot_rad), robot_pos[1] + dx*math.sin(robot_rot_rad) + dy*math.cos(robot_rot_rad))
        obj_vec = np.subtract(reef_pos,cameraPos)
        
        obj_ang = np.arctan2(obj_vec[1],obj_vec[0])
        cam_ang = robot_rot_rad + robot_yaw_offset_rad
        D_ang = obj_ang-cam_ang

        Vx = reef_pos[0] + reef_radius * math.cos(D_ang+math.pi)
        Vy = reef_pos[1] + reef_radius * math.sin(D_ang+math.pi)
        return (Vx,Vy)

    while True:
        frame = np.zeros((size_y,size_x,3),dtype=np.uint8)

        cv2.circle(frame,reef_center,reef_radius,(0,255,0))

        robot_rot = 0

        drawRobot(frame,robot_width,robot_height,robot_pos[0],robot_pos[1],robot_rot)
        
        seenPoint = calculateSeenPoint(reef_center,reef_radius,robot_pos,robot_rot,robot_cam_offset,robot_yaw_offset_rad)
        if seenPoint is not None:
            cv2.circle(frame,tuple(map(int,seenPoint)),10,(255,0,0),-1)
        
        cv2.imshow(title,frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()
