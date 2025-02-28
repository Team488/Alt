from typing import Any
import pyrealsense2 as rs
import numpy as np
import cv2
from tools.Constants import CameraIntrinsics, D435IResolution
from tools import calibration


class realsense2Helper:
    DEPTH = 0
    COLOR = 1

    def __init__(self, res: D435IResolution) -> None:
        self.pipeline = rs.pipeline()
        self.config = rs.config()
        self.streams = [rs.stream.depth, rs.stream.color]
        self.formats = [rs.format.z16, rs.format.bgr8]
        for format, stream in zip(self.formats, self.streams):
            self.config.enable_stream(stream, res.w, res.h, format, res.fps)

        pipeline_profile = self.pipeline.start(self.config)

        self.baked = []
        self.maps = []
        for stream in self.streams:
            intr, coeffs = self.__getBakedIntrinsics(pipeline_profile, stream)
            mapx, mapy = calibration.createMapXYForUndistortion(
                distCoeffs=coeffs, cameraIntrinsics=intr
            )

            self.baked.append((intr, coeffs))
            self.maps.append((mapx, mapy))

    def __getBakedIntrinsics(
        self, pipeline_profile, rs_stream
    ) -> tuple[CameraIntrinsics, list]:

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

        return intr, np.array(intrinsics.coeffs, dtype=np.float32)

    def __dewarp(self, frame, stream_idx):
        mapx, mapy = self.maps[stream_idx]
        return calibration.undistortFrame(frame, mapx, mapy)

    def getCameraIntrinsics(self, stream_idx=COLOR) -> CameraIntrinsics:
        return self.baked[stream_idx][0]

    def getDepthAndColor(self):
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

    def close(self):
        self.pipeline.stop()

    def isOpen(self) -> bool:
        device = self.pipeline.get_active_profile().get_device()
        if device is not None:
            return device.is_connected()

        return False
