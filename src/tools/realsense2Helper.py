from typing import Any, Tuple, List, Optional, Union
import pyrealsense2 as rs
import numpy as np
import cv2
from tools.Constants import CameraIntrinsics, D435IResolution
from tools import calibration


class realsense2Helper:
    """
    Helper class for interacting with Intel RealSense D435i depth camera
    """
    DEPTH = 0
    COLOR = 1

    def __init__(self, res: D435IResolution) -> None:
        """
        Initialize the RealSense camera with the specified resolution
        
        Args:
            res: The resolution settings for the camera
        """
        self.res = res
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.streams = [rs.stream.depth, rs.stream.color]
        self.formats = [rs.format.z16, rs.format.bgr8]
        
        # Enable streams with the specified resolution
        for format, stream in zip(self.formats, self.streams):
            self.config.enable_stream(stream, res.w, res.h, format, res.fps)

        pipeline_profile = self.pipeline.start(self.config)

        # Store intrinsics and undistortion maps for each stream
        self.baked: List[Tuple[CameraIntrinsics, np.ndarray]] = []
        self.maps: List[Tuple[np.ndarray, np.ndarray]] = []
        
        for stream in self.streams:
            intr, coeffs = self.__getBakedIntrinsics(pipeline_profile, stream)
            mapx, mapy = calibration.createMapXYForUndistortion(
                distCoeffs=coeffs, cameraIntrinsics=intr
            )

            self.baked.append((intr, coeffs))
            self.maps.append((mapx, mapy))

    def getFps(self) -> int:
        """
        Get the frames per second setting of the camera
        
        Returns:
            The FPS value
        """
        return self.res.fps

    def __getBakedIntrinsics(
        self, pipeline_profile: Any, rs_stream: Any
    ) -> Tuple[CameraIntrinsics, np.ndarray]:
        """
        Get the intrinsics and distortion coefficients for a RealSense stream
        
        Args:
            pipeline_profile: The RealSense pipeline profile
            rs_stream: The RealSense stream to get intrinsics for
            
        Returns:
            A tuple containing (camera_intrinsics, distortion_coefficients)
        """
        intrinsics = (
            pipeline_profile.get_stream(rs_stream)
            .as_video_stream_profile()
            .get_intrinsics()
        )

        print(f"Width: {intrinsics.width}, Height: {intrinsics.height}")
        print(f"fx: {intrinsics.fx}, fy: {intrinsics.fy}")
        print(f"cx: {intrinsics.ppx}, cy: {intrinsics.ppy}")
        print(f"Distortion Model: {intrinsics.model}")
        print(f"Distortion Coefficients: {intrinsics.coeffs}")
        intr = CameraIntrinsics(
            hres_pix=intrinsics.width,
            vres_pix=intrinsics.height,
            cx_pix=intrinsics.ppx,
            cy_pix=intrinsics.ppy,
            fx_pix=intrinsics.fx,
            fy_pix=intrinsics.fy,
        )

        # Return as ndarray instead of list
        return intr, np.array(intrinsics.coeffs, dtype=np.float32)

    def __dewarp(self, frame: np.ndarray, stream_idx: int) -> np.ndarray:
        """
        Dewarp a frame using the calibration maps
        
        Args:
            frame: The frame to dewarp
            stream_idx: The index of the stream (DEPTH or COLOR)
            
        Returns:
            The dewarped frame
        """
        mapx, mapy = self.maps[stream_idx]
        return calibration.undistortFrame(frame, mapx, mapy)

    def getCameraIntrinsics(self, stream_idx: int = COLOR) -> CameraIntrinsics:
        """
        Get the camera intrinsics for a stream
        
        Args:
            stream_idx: The index of the stream (DEPTH or COLOR)
            
        Returns:
            The camera intrinsics
        """
        return self.baked[stream_idx][0]

    def getDepthAndColor(self) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """
        Get the depth and color frames from the camera
        
        Returns:
            A tuple containing (depth_image, color_image) or None if either frame is missing
        """
        frames = self.pipeline.wait_for_frames()
        depth_frame = frames.get_depth_frame()
        color_frame = frames.get_color_frame()
        if not depth_frame or not color_frame:
            return None

        depth_image = np.asanyarray(depth_frame.get_data())
        depth_image = self.__dewarp(depth_image, self.DEPTH)
        color_image = np.asanyarray(color_frame.get_data())
        color_image = self.__dewarp(color_image, self.COLOR)
        return depth_image, color_image

    def close(self) -> None:
        """
        Stop the camera pipeline
        """
        self.pipeline.stop()

    def isOpen(self) -> bool:
        """
        Check if the camera is connected and the pipeline is active
        
        Returns:
            True if the camera is connected, False otherwise
        """
        try:
            device = self.pipeline.get_active_profile().get_device()
            if device is not None:
                return device.is_connected()
        except Exception:
            return False
            
        return False
