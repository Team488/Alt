import numpy as np
import depthai as dai

from ...Parameters.CameraIntrinsics import CameraIntrinsics
from ...Constants.resolution import OAKDLITEResolution
from Alt.Core import getChildLogger

Sentinel = getChildLogger("DepthAiHelper")


class DepthAIHelper:
    def __init__(self, res: OAKDLITEResolution) -> None:
        self.pipeline = dai.Pipeline()
        self.res = res  # Store resolution info
        self.device = None
        self.load_pipeline(self.pipeline, res)
        self.device = dai.Device(self.pipeline)
        self.intrColor = self.__getBakedIntrinsics(
            dai.CameraBoardSocket.RGB, self.device, res
        )
        self.color_queue = self.device.getOutputQueue(
            name="video", maxSize=4, blocking=False
        )
        self.depth_queue = self.device.getOutputQueue(
            name="depth", maxSize=4, blocking=False
        )

    def getFps(self):
        return self.res.fps

    def __getBakedIntrinsics(
        self,
        camera_id: dai.CameraBoardSocket,
        device: dai.Device,
        res: OAKDLITEResolution,
    ) -> None:
        calibData = device.readCalibration()
        intrinsics = calibData.getCameraIntrinsics(camera_id, res.w, res.h)
        intrinsic_matrix = np.array(intrinsics).reshape(3, 3)

        fx = intrinsic_matrix[0][0]
        fy = intrinsic_matrix[1][1]

        cx = intrinsic_matrix[0][2]
        cy = intrinsic_matrix[1][2]

        intr = CameraIntrinsics(
            width_pix=res.w, height_pix=res.h, fx_pix=fx, fy_pix=fy, cx_pix=cx, cy_pix=cy
        )
        return intr

    def getColorIntrinsics(self) -> CameraIntrinsics:
        return self.intrColor

    def load_pipeline(self, pipeline: dai.Pipeline, res: OAKDLITEResolution) -> None:
        if res == OAKDLITEResolution.OAK1080P:
            sensor_res = dai.ColorCameraProperties.SensorResolution.THE_1080_P
        else:
            # OAKDLITEResolution.OAK4K
            sensor_res = dai.ColorCameraProperties.SensorResolution.THE_4_K

        # color camera
        cam_rgb = pipeline.create(dai.node.ColorCamera)
        rgbOut = pipeline.create(dai.node.XLinkOut)

        cam_rgb.setResolution(sensor_res)
        cam_rgb.setFps(res.fps)
        cam_rgb.setVideoSize(res.w, res.h)
        cam_rgb.initialControl.setManualFocus(
            1
        )  # Disable autofocus (0 - 255) larger = closer focus
        cam_rgb.video.link(rgbOut.input)
        rgbOut.setStreamName("video")

        # Depth Processing
        monoLeft = pipeline.create(dai.node.MonoCamera)
        monoRight = pipeline.create(dai.node.MonoCamera)
        stereo = pipeline.create(dai.node.StereoDepth)

        cam_rgb.setBoardSocket(dai.CameraBoardSocket.RGB)  # RGB camera

        monoLeft.setCamera("left")
        monoRight.setCamera("right")
        monoLeft.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)
        monoRight.setResolution(dai.MonoCameraProperties.SensorResolution.THE_400_P)

        stereo.setDefaultProfilePreset(dai.node.StereoDepth.PresetMode.HIGH_DENSITY)
        stereo.setLeftRightCheck(True)
        stereo.setDepthAlign(dai.CameraBoardSocket.CAM_A)

        # stereo.setOutputSize(monoLeft.getResolutionWidth(), monoLeft.getResolutionHeight())
        stereo.setSubpixel(True)

        monoLeft.out.link(stereo.left)
        monoRight.out.link(stereo.right)

        # ---- Depth Image Resizing ----
        depthManip = pipeline.create(dai.node.ImageManip)
        depthManip.setResize(res.w, res.h)  # Match RGB res
        depthManip.setKeepAspectRatio(True)  # Force full resize
        depthManip.setMaxOutputFrameSize(res.w * res.h * 2)

        stereo.depth.link(depthManip.inputImage)

        # Depth output
        xoutDepth = pipeline.create(dai.node.XLinkOut)
        xoutDepth.setStreamName("depth")
        depthManip.out.link(xoutDepth.input)  # Output resized depth

    def getColorFrame(self) -> np.ndarray:
        if self.device is not None:
            frame = self.color_queue.get()
            if frame is not None:
                return frame.getCvFrame()
        return None

    def getDepthFrame(self) -> np.ndarray:
        """Returns the depth frame as a NumPy array, resized to match the RGB frame."""
        if self.device is not None:
            depth_frame = self.depth_queue.get()
            if depth_frame is not None:
                depth_frame = depth_frame.getFrame()
                depth_downscaled = depth_frame[::4]
                if np.all(depth_downscaled == 0):
                    min_depth = 0  # Set a default minimum depth value when all elements are zero
                else:
                    min_depth = np.percentile(
                        depth_downscaled[depth_downscaled != 0], 1
                    )
                max_depth = np.percentile(depth_downscaled, 99)
                depthFrameColor = np.interp(
                    depth_frame, (min_depth, max_depth), (0, 255)
                ).astype(np.uint8)
                # depthFrameColor = cv2.applyColorMap(depthFrameColor, cv2.COLORMAP_HOT)
                return depthFrameColor
        return None

    def close(self) -> None:
        """Properly release resources."""
        self.color_queue.close()
        self.depth_queue.close()
        self.device.close()

    def isOpen(self) -> bool:
        return self.device and not self.device.isClosed()
