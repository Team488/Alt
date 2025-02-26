import time
import cv2
from abstract.Agent import Agent
from coreinterface.FramePacket import FramePacket
from tools.Constants import CameraIntrinsics
from tools.depthAiHelper import DepthAIHelper
from screeninfo import get_monitors


def getPrimary():
    mons = get_monitors()
    for monitor in mons:
        if monitor.is_primary:
            return monitor
    return None


class CameraUsingAgentBase(Agent):
    FRAMEPOSTFIX = "Frame"

    """Agent -> CameraUsingAgentBase

    Adds camera ingestion capabilites to an agent. When used with a localizing agent, it matches timestamps aswell
    NOTE: Requires extra arguments passed in somehow and you should always be extending this class, and use partial constructors further up
    NOTE: This means you cannot run this class as is
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.cameraIntrinsics = kwargs.get("cameraIntrinsics", None)
        self.cameraPath = kwargs.get("cameraPath", None)
        self.showFrames = kwargs.get("showFrames", False)
        self.hasIngested = False
        self.exit = False
        self.WINDOWNAME = "frame"
        self.primaryMonitor = getPrimary()

    def create(self):
        super().create()
        # self.xdashDebugger = XDashDebugger()
        self.oakMode = self.cameraPath == "oakdlite"
        if self.oakMode:
            self.cap = DepthAIHelper(self.cameraIntrinsics)
        else:
            self.cap = cv2.VideoCapture(self.cameraPath)
            if self.cameraIntrinsics is not None:
                fourcc = cv2.VideoWriter_fourcc(*"MJPG")  # or 'XVID', 'MP4V'
                self.cap.set(cv2.CAP_PROP_FOURCC, fourcc)
                CameraIntrinsics.setCapRes(self.cameraIntrinsics, self.cap)
            else:
                self.Sentinel.warning(
                    "Camera intrinsics is None! Cap properties will not be set."
                )

        self.testCapture()

        self.sendFrame = self.propertyOperator.createProperty(
            "Send-Frame", False, loadIfSaved=False
        )  # this is one of those properties that should always be opt-in Eg reset after restart

        self.frameProp = self.propertyOperator.createCustomReadOnlyProperty(
            self.FRAMEPOSTFIX, b""
        )

        if self.showFrames:
            cv2.namedWindow(self.WINDOWNAME, cv2.WINDOW_AUTOSIZE)

    def testCapture(self):
        retTest = True

        if self.oakMode:
            try:
                frame = self.cap.getFrame()
                if frame is None:
                    retTest = False
            except Exception as e:
                self.Sentinel.debug(e)
        else:

            if self.cap.isOpened():
                retTest, _ = self.cap.read()
            else:
                retTest = False

        if not retTest:
            raise BrokenPipeError(
                f"Failed to read from camera! {self.cameraPath=} {self.oakMode=}"
            )

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
                    self.latestFrame = cv2.resize(
                        self.latestFrame,
                        (self.primaryMonitor.width, self.primaryMonitor.height),
                    )
                cv2.imshow(self.WINDOWNAME, self.latestFrame)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.exit = True

            # network showing of frame
            if self.sendFrame.get():
                framePacket = FramePacket.createPacket(
                    time.time() * 1000, "Frame", self.latestFrame
                )
                self.frameProp.set(framePacket.to_bytes())

        with self.timer.run("cap_read"):
            self.hasIngested = True
            # stime = time.time()
            # while self.cap.grab():
            #     if time.time() - stime > 0.050:  # Timeout after 100ms
            #         self.Sentinel.warning("Skipping buffer due to timeout.")
            #         break

            if self.oakMode:
                frame = self.cap.getFrame()
            else:
                ret, frame = self.cap.read()

                if not ret:
                    raise BrokenPipeError("Camera ret is false!")

            self.latestFrame = self.preprocessFrame(frame)

    def onClose(self):
        super().onClose()
        if self.oakMode:
            self.cap.close()
        else:
            if self.cap.isOpened():
                self.cap.release()

        if self.showFrames:
            cv2.destroyAllWindows()

    def isRunning(self):
        if not self.oakMode and not self.cap.isOpened():
            self.Sentinel.fatal("Camera cant be opened!")
            return False
        if self.exit:
            self.Sentinel.info("Gracefully exiting...")
            return False
        return True

    def forceShutdown(self):
        super().forceShutdown()
        self.cap.release()
