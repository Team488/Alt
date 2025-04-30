

class CameraConfig:
    def __init__(self, width : int, height : int, fps : int = None, videoWriter : str = None):
        self.width = width
        self.height = height
        self.fps = fps
        self.videoWriter = videoWriter

    # def setOpenCVCap(self, cap : OpenCVCapture) -> bool:
    #     paramSet = cap.setWidth(self.width)
    #     paramSet = paramSet and cap.setHeight(self.width)
    #     if self.fps is not None:
    #         paramSet = paramSet and cap.setFps(self.fps)
    #     if self.videoWriter is not None:
    #         paramSet = paramSet and cap.setVideoWriter(self.videoWriter)

    #     return paramSet


        