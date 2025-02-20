import time
import cv2
from abstract.Agent import Agent

class CameraUsingAgentBase(Agent):
    """Agent -> CameraUsingAgentBase

    Adds camera ingestion capabilites to an agent. When used with a localizing agent, it matches timestamps aswell
    NOTE: Requires extra arguments passed in somehow and you should always be extending this class, and use partial constructors further up
    NOTE: This means you cannot run this class as is
    """


    def __init__(
        self,
        cameraPath: str,
        showFrames: bool = False
    ):
        super().__init__()
        self.cameraPath = cameraPath
        self.showFrames = showFrames
        self.hasIngested = False
        self.exit = False

    def create(self):
        super().create()
        # self.xdashDebugger = XDashDebugger()
        self.cap = cv2.VideoCapture(self.cameraPath)
        retTest = True
        if self.cap.isOpened():
            retTest, _ = self.cap.read()

        if not self.cap.isOpened() or not retTest:
            raise BrokenPipeError("Failed to open camera!")


    def runPeriodic(self):
        super().runPeriodic()
        # show last frame if enabled. This allows any drawing that might have been on the frame to be shown
        if self.showFrames and self.hasIngested:
            cv2.imshow("frame",self.latestFrame)

            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.exit = True


        with self.timer.run("cap_read"):
            self.hasIngested = True
            stime = time.time()
            # while self.cap.grab():
            #     if time.time() - stime > 0.050:  # Timeout after 100ms
            #         self.Sentinel.warning("Skipping buffer due to timeout.")
            #         break
            ret, frame = self.cap.read()
            self.latestFrame = frame

        if not ret:
            if self.cap.isOpened():
                self.cap.release()
            raise BrokenPipeError("Camera ret is false!")
        


    def onClose(self):
        super().onClose()
        if self.cap.isOpened():
            self.cap.release()

        if self.showFrames:
            cv2.destroyAllWindows()

    def isRunning(self):
        if not self.cap.isOpened():
            self.Sentinel.fatal("Camera cant be opened!")
            return False
        if self.exit:
            self.Sentinel.info("Gracefully exiting...")
            return False
        return True

    def forceShutdown(self):
        super().forceShutdown()
        self.cap.release()