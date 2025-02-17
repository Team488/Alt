import math
import cv2
import numpy as np
from tools.Constants import CameraExtrinsics, MapConstants, CameraIntrinsicsPredefined

class ReefPositioner:
    def __init__(self, bluereef_center_cm = MapConstants.b_reef_center.getCM(), redreef_center_cm=MapConstants.r_reef_center.getCM(), reef_radius_cm=MapConstants.reefRadius.getCM(), num_post_groups = 6):
        self.b_reef_center = bluereef_center_cm
        self.r_reef_center = redreef_center_cm
        self.reef_radius = reef_radius_cm
        self.postsPerAngleRad = math.radians(360/num_post_groups)
    
    # wraps an angle between +-pi (instead of 0-2pi)
    def __wrap(self,ang):
        mod = ang % (2 * math.pi)
        if mod > math.pi:
            # wrap as negative
            return (2*math.pi)-mod
        return mod
    
    def __calculateSeenPostAng(self,reef_pos,robot_pos,robot_rot_rad,robotcam_offsetXY_cm,robotcam_yaw_rad,robotcam_fov_rad):
        dx = robotcam_offsetXY_cm[0]
        dy = robotcam_offsetXY_cm[1]
        cameraPos = (robot_pos[0] + dx*math.cos(robot_rot_rad)-dy*math.sin(robot_rot_rad), robot_pos[1] + dx*math.sin(robot_rot_rad) + dy*math.cos(robot_rot_rad))
        obj_vec = np.subtract(reef_pos,cameraPos)
        
        obj_ang = np.arctan2(obj_vec[1],obj_vec[0])
        cam_ang = robot_rot_rad + robotcam_yaw_rad

        D_ang = (obj_ang-cam_ang)

        if abs(self.__wrap(D_ang)) > robotcam_fov_rad/2:
            # out of view
            return None

        final_ang = obj_ang + math.pi
        post_idx = round((final_ang % (2 * math.pi))/(self.postsPerAngleRad)) # round to the nearest post (assuming 0 deg = post 0)

        # handle wrapping in the case the angle is close to 2pi -> 0 (since they are the same we dont want two different ids)
        post_idx %= 6

        return final_ang, post_idx
    
    """ 
        Takes robot position and camera information, and returns a sets of coordinates representing the point of the reef seen and the closest posts
        If the camera is not in the field of view of the reef, the function returns None
        If the camera is in view, it returns the coordinate of the reef it sees, and also the closest reef post idx
    """
    def getPostCoordinates(self,isBlueReef : bool, robot_pos_cm : tuple[int,int],robot_rot_rad : float,robotcam_offsetXY_cm : tuple[int,int],robotcam_yaw_rad : float,robotcam_fov_rad : float):
        reef_center = self.b_reef_center if isBlueReef else self.r_reef_center
        res = self.__calculateSeenPostAng(reef_center,robot_pos_cm,robot_rot_rad,robotcam_offsetXY_cm,robotcam_yaw_rad,robotcam_fov_rad)
        if res is None:
            return None
        ang, post_idx = res
        x = reef_center[0] + math.cos(ang)*self.reef_radius
        y = reef_center[1] + math.sin(ang)*self.reef_radius
        return x,y,post_idx
    
    def getPostCoordinatesWconst(self,isBlueReef : bool, robot_pos_cm : tuple[int,int],robot_rot_rad : float,camera_extr : CameraExtrinsics,camera_intr : CameraIntrinsicsPredefined):
        return self.getPostCoordinates(isBlueReef,robot_pos_cm,robot_rot_rad,(camera_extr.getOffsetXCM(),camera_extr.getOffsetYCM()),camera_extr.getYawOffsetAsRadians(),camera_intr.getHFovRad())