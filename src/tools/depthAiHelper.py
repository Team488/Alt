import numpy as np
import cv2
import depthai as dai

from tools.Constants import CameraIntrinsics, CameraIntrinsicsPredefined
from Core import getLogger

Sentinel = getLogger("DepthAiHelper")


class DepthAIHelper:
    def __init__(self, cameraIntrinsics: CameraIntrinsics):

        self.pipeline = dai.Pipeline()
        if self.load_pipeline(self.pipeline, cameraIntrinsics):
            self.device = dai.Device(self.pipeline)
            self.color_queue = self.device.getOutputQueue(
                name="video", maxSize=4, blocking=False
            )
        else:
            Sentinel.warning(
                "Please adjust camera intrinsics to be a valid oakdlite config!"
            )

    def load_pipeline(self, pipeline: dai.Pipeline, cameraIntrinsics: CameraIntrinsics):
        # Define color camera
        cam_rgb = pipeline.create(dai.node.ColorCamera)
        xoutVideo = pipeline.create(dai.node.XLinkOut)
        xoutVideo.setStreamName("video")

        cam_rgb.setBoardSocket(dai.CameraBoardSocket.CAM_A)  # rgb (b,c is stereo)

        res = None
        if cameraIntrinsics == CameraIntrinsicsPredefined.OAKDLITE1080P:
            res = dai.ColorCameraProperties.SensorResolution.THE_1080_P
        elif cameraIntrinsics == CameraIntrinsicsPredefined.OAKDLITE4K:
            res = dai.ColorCameraProperties.SensorResolution.THE_4_K
        if res == None:
            Sentinel.fatal(
                "Invalid depth ai camera intrinsics passed in! Must be one of the ones with oakdlite in it"
            )
            return False

        cam_rgb.setResolution(res)
        cam_rgb.setFps(60)  # will max out whatever the max of the res is
        cam_rgb.setVideoSize(cameraIntrinsics.getHres(), cameraIntrinsics.getVres())
        # Create an XLink output to send the frames to the host
        cam_rgb.video.link(xoutVideo.input)

        return True

    def getFrame(self) -> np.ndarray:
        frame = self.color_queue.get()
        if frame is not None:
            return frame.getCvFrame()
        return None

    @staticmethod
    def getCameraIntrinsicDump(res=None):
        import depthai as dai

        device = dai.Device()  # Create device
        try:
            calibData = device.readCalibration()
            cameras = device.getConnectedCameras()

            for cam in cameras:
                M, width, height = calibData.getDefaultIntrinsics(cam)
                M = np.array(M)
                print(f"Camera Name: {cam}")
                print(f"Camera Matrix: {M} \nWidth: {width}, Height: {height}")

        finally:
            device.close()  # Ensure the device is closed

    def close(self):
        """Properly release resources."""
        self.color_queue.close()
        self.device.close()
