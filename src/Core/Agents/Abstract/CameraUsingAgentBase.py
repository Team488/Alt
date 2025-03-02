import time
from typing import Union
import cv2
from abstract.Agent import Agent
from abstract.Capture import Capture
from coreinterface.FramePacket import FramePacket
from tools.Constants import CameraIntrinsics
from tools.depthAiHelper import DepthAIHelper
from screeninfo import get_monitors
from abstract.depthCamera import depthCamera


def getPrimary():
    mons = get_monitors()
    for monitor in mons:
        if monitor.is_primary:
            return monitor
    return None


class CameraUsingAgentBase(Agent):
    FRAMEPOSTFIX = "Frame"
    FRAMETOGGLEPOSTFIX = "SendFrame"
    RUNNINGHOSTNAMES = "RUNNINGHOSTNAMES"

    """Agent -> CameraUsingAgentBase

    Adds camera ingestion capabilites to an agent. When used with a localizing agent, it matches timestamps aswell
    NOTE: Requires extra arguments passed in somehow and you should always be extending this class, and use partial constructors further up
    NOTE: This means you cannot run this class as is
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.cameraIntrinsics = kwargs.get("cameraIntrinsics", None)
        self.capture: Union[Capture, depthCamera] = kwargs.get("capture", None)
        self.depthEnabled = issubclass(self.capture.__class__, depthCamera)
        self.showFrames = kwargs.get("showFrames", False)
        self.hasIngested = False
        self.exit = False
        self.WINDOWNAMEDEPTH = "depth_frame"
        self.WINDOWNAMECOLOR = "color_frame"
        # self.primaryMonitor = getPrimary()
        self.primaryMonitor = None

    def updateFrameHostnames(self):
        existingHostnames: list = self.xclient.getStringList(self.RUNNINGHOSTNAMES)
        if existingHostnames is None:
            existingHostnames = []  # "default arg"
        baseHostName = self.propertyOperator.getFullPrefix()
        if baseHostName not in existingHostnames:
            existingHostnames.append(baseHostName)

        self.xclient.putStringList(self.RUNNINGHOSTNAMES, existingHostnames)

    def create(self) -> None:
        super().create()

        self.updateFrameHostnames()
        # self.xdashDebugger = XDashDebugger()

        self.testCapture()

        self.sendFrame = self.propertyOperator.createProperty(
            "SendFrame",
            False,
            loadIfSaved=False,
            isCustom=True,
            addBasePrefix=True,
            addOperatorPrefix=True,
        )  # this is one of those properties that should always be opt-in Eg reset after restart

        self.frameProp = self.propertyOperator.createCustomReadOnlyProperty(
            self.FRAMEPOSTFIX, b"", addBasePrefix=True, addOperatorPrefix=True
        )

        if self.showFrames:
            cv2.namedWindow(self.WINDOWNAMECOLOR)

            if self.depthEnabled:
                cv2.namedWindow(self.WINDOWNAMEDEPTH)

    def testCapture(self):
        if self.capture.isOpen():
            frame = self.capture.getColorFrame()
            retTest = frame is not None

        else:
            retTest = False

        if not retTest:
            raise BrokenPipeError(f"Failed to read from camera! {type(self.capture)=}")

    def preprocessFrame(self, frame):
        """Optional method you can implement to add preprocessing to a frame"""
        return frame

    def runPeriodic(self):
        super().runPeriodic()
        # show last frame if enabled. This allows any drawing that might have been on the frame to be shown
        if self.hasIngested:
            # local showing of frame
            if self.showFrames:
                if self.primaryMonitor:
                    self.latestFrameCOLOR = cv2.resize(
                        self.latestFrameCOLOR,
                        (self.primaryMonitor.width, self.primaryMonitor.height),
                    )

                    if self.latestFrameDEPTH is not None:
                        self.latestFrameDEPTH = cv2.resize(
                            self.latestFrameDEPTH,
                            (self.primaryMonitor.width, self.primaryMonitor.height),
                        )

                cv2.imshow(self.WINDOWNAMECOLOR, self.latestFrameCOLOR)

                if self.latestFrameDEPTH is not None:
                    cv2.imshow(self.WINDOWNAMEDEPTH, self.latestFrameDEPTH)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.exit = True

            # network showing of frame
            if self.sendFrame.get():
                framePacket = FramePacket.createPacket(
                    time.time() * 1000, "Frame", self.latestFrameCOLOR
                )
                self.frameProp.set(framePacket.to_bytes())

        with self.timer.run("cap_read"):
            self.hasIngested = True

            if self.depthEnabled:
                latestFrames = self.capture.getDepthAndColorFrame()
                if latestFrames is None:
                    raise BrokenPipeError("Camera failed to capture with depth!")

                self.latestFrameDEPTH = latestFrames[0]
                self.latestFrameCOLOR = self.preprocessFrame(latestFrames[1])

            else:
                frame = self.capture.getColorFrame()
                if frame is None:
                    raise BrokenPipeError("Camera failed to capture!")

                self.latestFrameCOLOR = self.preprocessFrame(frame)
                self.latestFrameDEPTH = None

    def onClose(self) -> None:
        super().onClose()
        self.capture.close()

        if self.showFrames:
            cv2.destroyAllWindows()

    def isRunning(self) -> bool:
        if not self.capture.isOpen():
            self.Sentinel.fatal("Camera cant be opened!")
            return False
        if self.exit:
            self.Sentinel.info("Gracefully exiting...")
            return False
        return True

    def forceShutdown(self) -> None:
        super().forceShutdown()
        self.capture.close()
