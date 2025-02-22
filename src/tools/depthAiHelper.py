import numpy as np
import cv2
import depthai as dai


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
        frame = self.color_queue.get()
        if frame is not None:
            return frame.getCvFrame()
        return None

    @staticmethod
    def getCameraIntrinsicDump(res=None):
        import depthaiTest as dai

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

