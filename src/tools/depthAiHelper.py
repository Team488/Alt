import numpy as np
import depthai as dai
import cv2


class DepthAIHelper:
    def __init__(self):
        self.pipeline = dai.Pipeline()
        self.load_pipeline(self.pipeline)
        self.device = dai.Device(self.pipeline)
        self.color_queue = self.device.getOutputQueue(
            name="video", maxSize=4, blocking=False
        )

    def load_pipeline(self, pipeline):
        # Define color camera
        cam_rgb = pipeline.create(dai.node.ColorCamera)
        cam_rgb.setBoardSocket(dai.CameraBoardSocket.RGB)
        cam_rgb.setResolution(
            dai.ColorCameraProperties.SensorResolution.THE_1080_P
        )  # Change as needed
        cam_rgb.setFps(30)  # Adjust FPS as required

        # Create an XLink output to send the frames to the host
        xout = pipeline.create(dai.node.XLinkOut)
        xout.setStreamName("video")
        cam_rgb.video.link(xout.input)

    def getFrame(self) -> np.ndarray:
        frame = self.video_queue.get().getCvFrame()
        return frame

    @staticmethod
    def getCameraIntrinsicDump(res=None):
        with dai.Device() as device:
            calibData = device.readCalibration()

            cameras = device.getConnectedCameras()

            for cam in cameras:
                M, width, height = calibData.getDefaultIntrinsics(cam)
                # intrinsics = calibData.getCameraIntrinsics(dai.CameraBoardSocket.RGB, 1920, 1080)

                M = np.array(M)
                print(f"Camera Name: {cam}")
                print(f"Camerera Matrix: {M} \n {width=} {height=}")
