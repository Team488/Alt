import datetime
import multiprocessing
import multiprocessing.connection
import multiprocessing.managers
import multiprocessing.queues
import os
import time
from typing import Union, Optional, Callable, Tuple, Any
import cv2
import numpy as np
from Captures.CameraCapture import ConfigurableCameraCapture
from abstract.Agent import Agent
from abstract.Capture import Capture
from coreinterface.FramePacket import FramePacket
from tools.Constants import CameraIntrinsics
from tools.AgentConstants import AgentCapabilites
from tools.depthAiHelper import DepthAIHelper
from abstract.depthCamera import depthCamera
from tools import calibration
from Core.ConfigOperator import staticLoad
import Core


class CameraUsingAgentBase(Agent):
    FRAMEPOSTFIX = "Frame"
    FRAMETOGGLEPOSTFIX = "SendFrame"
    CALIBTOGGLEPOSTFIX = "StartCalib"
    CALIBIDEALSHAPEWPOSTFIX = "CALIBGOALSHAPEW"
    CALIBIDEALSHAPEHPOSTFIX = "CALIBGOALSHAPEH"
    CALIBIDEALCOUNT = "NUMCALIBPICTURES"
    DEFAULTCALIBCOUNT = 100
    CALIBRATIONPREFIX = "Calibrations"

    """Agent -> CameraUsingAgentBase

    Adds camera ingestion capabilites to an agent. When used with a localizing agent, it matches timestamps aswell
    NOTE: Requires extra arguments passed in somehow and you should always be extending this class, and use partial constructors further up
    NOTE: This means you cannot run this class as is
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.capture: Union[
            Capture, depthCamera, ConfigurableCameraCapture
        ] = kwargs.get("capture", None)
        if self.capture is None:
            raise ValueError("CameraUsingAgentBase requires a capture object")

        self.depthEnabled: bool = issubclass(self.capture.__class__, depthCamera)
        self.iscv2Configurable: bool = issubclass(
            self.capture.__class__, ConfigurableCameraCapture
        )
        self.customLoaded: bool = False
        self.preprocessFrame: Optional[Callable[[np.ndarray], np.ndarray]] = None
        self.calibMTime: Union[float, str] = "Not_Set"

        if self.iscv2Configurable:
            # try and load a possible saved calibration
            calibPath = f"{os.path.join(self.CALIBRATIONPREFIX, self.capture.getUniqueCameraIdentifier())}.json"

            out = staticLoad(calibPath)
            if out:
                calib, self.calibMTime = out
                self.customLoaded = True
                newCameraIntrinsics = CameraIntrinsics.fromCustomConfigLoaded(calib)
                mapx, mapy = calibration.createMapXYForUndistortionFromCalib(calib)
                self.preprocessFrame = lambda frame: calibration.undistortFrame(
                    frame, mapx, mapy
                )
                self.capture.updateIntrinsics(newCameraIntrinsics)
            else:
                self.calibMTime = "Not_Loaded!"
                self.customLoaded = False

        else:
            if self.depthEnabled:
                self.calibMTime = "Prebaked_Internally"
            else:
                self.calibMTime = "Not_Using_Intrinsics"

        self.showFrames: bool = kwargs.get("showFrames", False)
        self.hasIngested: bool = False
        self.exit: bool = False
        self.WINDOWNAMEDEPTH: str = "depth_frame"
        self.WINDOWNAMECOLOR: str = "color_frame"
        self.latestFrameDEPTH: Optional[np.ndarray] = None
        self.latestFrameMain: Optional[np.ndarray] = None
        self.sendFrame: bool = False
        self.calib: bool = False

    def sendInitialUpdate(self) -> None:
        """Set up initial camera intrinsics properties"""
        if self.propertyOperator is None:
            raise ValueError("PropertyOperator not initialized")

        if self.iscv2Configurable:
            self.Sentinel.info("Detected cv2 configurable capture..")
            if self.customLoaded:
                self.Sentinel.info("Custom loaded config!")
            else:
                self.Sentinel.info("Could not find custom camera config")

            self.propertyOperator.createReadOnlyProperty("CameraIntrinsics", "").set(
                str(self.capture.getIntrinsics())
            )
        elif self.depthEnabled:
            self.Sentinel.info("Depth camera detected..")
            self.propertyOperator.createReadOnlyProperty("CameraIntrinsics", "").set(
                str(self.capture.getIntrinsics())
            )

        if isinstance(self.calibMTime, float):
            readable_time = datetime.datetime.fromtimestamp(self.calibMTime).strftime(
                "%Y-%m-%d %H:%M:%S"
            )
            self.propertyOperator.createReadOnlyProperty(
                "CameraIntrinsics.LastModification", ""
            ).set(readable_time)
        else:
            # already str
            self.propertyOperator.createReadOnlyProperty(
                "CameraIntrinsics.LastModification", ""
            ).set(self.calibMTime)

    def create(self) -> None:
        super().create()
        if not Core.canCurrentlyDisplay:
            self.Sentinel.warning("This enviorment cannot display frames!")
            self.showFrames = False

        self.capture.create()
        self.sendInitialUpdate()

        # if we are not main thread, even if it says showframe true we cannot allow it
        if not self.isMainThread:
            if self.Sentinel:
                self.Sentinel.warning(
                    "When an agent is not running on the main thread, it cannot display frames directly."
                )
            self.showFrames = False

        # self.xdashDebugger = XDashDebugger()

        self.testCapture()

        if self.updateOp is None:
            raise ValueError("UpdateOperator not initialized")

        self.sendFrameProp = self.updateOp.createGlobalUpdate(
            self.FRAMETOGGLEPOSTFIX, default=False, loadIfSaved=False
        )
        self.calibProp = self.updateOp.createGlobalUpdate(
            self.CALIBTOGGLEPOSTFIX, default=False, loadIfSaved=False
        )
        self.calibW = self.updateOp.createGlobalUpdate(
            self.CALIBIDEALSHAPEHPOSTFIX, default=None, loadIfSaved=False
        )
        self.calibH = self.updateOp.createGlobalUpdate(
            self.CALIBIDEALSHAPEWPOSTFIX, default=None, loadIfSaved=False
        )
        self.calibCount = self.updateOp.createGlobalUpdate(
            self.CALIBIDEALCOUNT, default=self.DEFAULTCALIBCOUNT, loadIfSaved=False
        )

        self.sendFrame = False
        self.calib = False

        if self.showFrames:
            cv2.namedWindow(self.WINDOWNAMECOLOR)

            if self.depthEnabled:
                cv2.namedWindow(self.WINDOWNAMEDEPTH)

        if AgentCapabilites.STREAM.objectName in self.extraObjects:
            self.stream_queue: multiprocessing.queues.Queue = self.extraObjects.get(
                AgentCapabilites.STREAM.objectName
            )

            streamPath = f"http://{Core.DEVICEIP}:5000/{self.agentName}/stream"

            self.propertyOperator.createCustomReadOnlyProperty(
                "stream.IP", streamPath, addBasePrefix=True, addOperatorPrefix=True
            )

            self.streamWidth = self.propertyOperator.createProperty(
                "stream.width", 320, isCustom=True, addOperatorPrefix=True
            )
            self.streamHeight = self.propertyOperator.createProperty(
                "stream.height", 180, isCustom=True, addOperatorPrefix=True
            )

        else:
            # raise better error
            raise RuntimeError(
                "FRAME QUEUE WAS NOT PROVIDED TO THE CAMERA USING AGENT! IT HAS STREAM CAPABILITES AND WAS EXPECTING IT"
            )

    def testCapture(self) -> None:
        """Test if the camera is properly functioning"""
        if self.capture.isOpen():
            frame = self.capture.getMainFrame()
            retTest = frame is not None
        else:
            retTest = False

        if not retTest:
            raise BrokenPipeError(f"Failed to read from camera! {type(self.capture)=}")

    def runPeriodic(self) -> None:
        super().runPeriodic()
        if not hasattr(self, "sendFrameProp") or not hasattr(self, "calibProp"):
            raise ValueError("Properties not initialized properly")

        self.sendFrame = self.sendFrameProp.get()
        self.calib = self.calibProp.get()

        if self.calib:

            if not self.iscv2Configurable:
                self.Sentinel.warning(
                    "Attempted to start calibration, but this capture type cannot be calibrated!"
                )
            else:
                w = self.calibW.get()
                if w is None:
                    # use default intrinsics width
                    w = self.capture.getIntrinsics().getHres()

                h = self.calibH.get()
                if h is None:
                    # use default intrinsics width
                    h = self.capture.getIntrinsics().getVres()

                numPics = self.calibCount.get()

                self.Sentinel.info(f"Starting Calibration! Goal Resolution: {w=} {h=}")
                calibrator = calibration.CustomCalibrator(
                    self.capture, timePerPicture=1, targetResolution=(w, h)
                )

                while calibrator.frameIdx < numPics:
                    frame = calibrator.calibrationCycle()
                    # send frame
                    framePacket = FramePacket.createPacket(
                        time.time() * 1000, "Frame", frame
                    )
                    self.updateOp.addGlobalUpdate(
                        self.FRAMEPOSTFIX, framePacket.to_bytes()
                    )

                    if self.showFrames:
                        cv2.imshow(self.WINDOWNAMECOLOR, frame)
                        if cv2.waitKey(1) & 0xFF == ord("q"):
                            self.exit = True
                            break

                    # if at any time calibprop becomes false, exit this loop and skip
                    if not self.calibProp.get():
                        break

                # only do if calib prop is still true
                if self.calibProp.get() and not self.exit:
                    shape = (h, w, 3)  # default

                    def runOnLoop(frame, frame_cnt):
                        cv2.putText(
                            frame,
                            f"Calibrating Frame Number {frame_cnt}/{numPics}...",
                            (20, 50),
                            1,
                            1,
                            (255, 255, 255),
                            1,
                        )

                        # send frame
                        framePacket = FramePacket.createPacket(
                            time.time() * 1000, "Frame", frame
                        )
                        self.updateOp.addGlobalUpdate(
                            self.FRAMEPOSTFIX, framePacket.to_bytes()
                        )
                        nonlocal shape
                        shape = frame.shape

                    uniqueCamIdentifier = self.capture.getUniqueCameraIdentifier()
                    calibPath = (
                        f"assets/{self.CALIBRATIONPREFIX}/{uniqueCamIdentifier}.json"
                    )
                    sucess = calibration.charuco_calibration(
                        calibPath=calibPath, runOnLoop=runOnLoop, arucoboarddim=(18, 11)
                    )

                    finalFrame = np.zeros(shape=shape, dtype=np.uint8)
                    if sucess:
                        cv2.putText(
                            finalFrame,
                            f"Finished calibration sucessfully!",
                            (20, 50),
                            1,
                            1,
                            (255, 255, 255),
                            1,
                        )
                    else:
                        cv2.putText(
                            finalFrame,
                            f"Failed to create calibration!",
                            (20, 50),
                            1,
                            1,
                            (255, 255, 255),
                            1,
                        )

                    framePacket = FramePacket.createPacket(
                        time.time() * 1000, "Frame", finalFrame
                    )
                    self.updateOp.addGlobalUpdate(
                        self.FRAMEPOSTFIX, framePacket.to_bytes()
                    )

            self.calib = False
            self.updateOp.addGlobalUpdate(
                self.CALIBTOGGLEPOSTFIX, False
            )  # force a false

        # show last frame if enabled. This allows any drawing that might have been on the frame to be shown
        if self.hasIngested:
            # local showing of frame
            if self.showFrames:
                cv2.imshow(self.WINDOWNAMECOLOR, self.latestFrameMain)

                if self.latestFrameDEPTH is not None:
                    cv2.imshow(self.WINDOWNAMEDEPTH, self.latestFrameDEPTH)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.exit = True

            # network showing of frame
            if self.sendFrame:
                framePacket = FramePacket.createPacket(
                    time.time() * 1000, "Frame", self.latestFrameMain
                )
                self.updateOp.addGlobalUpdate(self.FRAMEPOSTFIX, framePacket.to_bytes())

            # send to mjpeg stream
            if (
                self.streamWidth.get() != self.latestFrameMain.shape[1]
                or self.streamHeight.get() != self.latestFrameMain.shape[0]
            ):
                resizedFrame = cv2.resize(
                    self.latestFrameMain,
                    (self.streamWidth.get(), self.streamHeight.get()),
                )
                self.stream_queue.put_nowait(resizedFrame)
            else:
                self.stream_queue.put_nowait(self.latestFrameMain)

        with self.timer.run("cap_read"):
            self.hasIngested = True

            if self.depthEnabled:
                latestFrames = self.capture.getDepthAndColorFrame()
                if latestFrames is None:
                    raise BrokenPipeError("Camera failed to capture with depth!")

                self.latestFrameDEPTH = latestFrames[0]

                if self.preprocessFrame is not None:
                    self.latestFrameMain = self.preprocessFrame(latestFrames[1])
                else:
                    self.latestFrameMain = latestFrames[1]

            else:
                frame = self.capture.getMainFrame()
                if frame is None:
                    raise BrokenPipeError("Camera failed to capture!")

                if self.preprocessFrame is not None:
                    self.latestFrameMain = self.preprocessFrame(frame)
                else:
                    self.latestFrameMain = frame

    def onClose(self) -> None:
        super().onClose()
        self.capture.close()

        if self.showFrames:
            cv2.destroyAllWindows()

    def isRunning(self) -> bool:
        if not self.capture.isOpen():
            if self.Sentinel:
                self.Sentinel.fatal("Camera cant be opened!")
            return False
        if self.exit:
            if self.Sentinel:
                self.Sentinel.info("Gracefully exiting...")
            return False
        return True

    def forceShutdown(self) -> None:
        super().forceShutdown()
        self.capture.close()
