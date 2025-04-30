import os
import time
import datetime
from typing import Union, Optional, Callable, Any
import cv2
import numpy as np

from Alt.Core.Agents import Agent
from Alt.Core.Constants.AgentConstants import ProxyType
from Alt.Core.Operators.StreamOperator import StreamProxy

from ..Captures.OpenCVCapture import OpenCVCapture
from ..Captures.Capture import Capture, CaptureWIntrinsics, ConfigurableCapture
from ..Captures.depthCamera import depthCamera
from ..Proto.FramePacket import FramePacket
from ..Parameters.CameraIntrinsics import CameraIntrinsics
from .. import canCurrentlyDisplay
from ..Captures.tools import calibration
from .CalibrationUtil import CalibrationUtil


class CameraUsingAgentBase(Agent):
    FRAMEPOSTFIX = "Frame"
    FRAMETOGGLEPOSTFIX = "SendFrame"
    CALIBTIMEPERPICTURE = "TimePerPictureS"
    CALIBTOGGLEPOSTFIX = "StartCalib"
    CALIBIDEALSHAPEWPOSTFIX = "CALIBGOALSHAPEW"
    CALIBIDEALSHAPEHPOSTFIX = "CALIBGOALSHAPEH"
    CALIBIDEALCOUNT = "NUMCALIBPICTURES"
    ISCHARUCOCALIB = "ISCHARUCOCALIB"
    DEFAULTCALIBCOUNT = 100
    CALIBRATIONPREFIX = "Calibrations"
    CAMERASTREAMNAME = "cameraStream"

    @classmethod
    def requestProxies(cls):
        super().requestProxies()
        super().addProxyRequest(cls.CAMERASTREAMNAME, ProxyType.STREAM)


    """Agent -> CameraUsingAgentBase

    Adds camera ingestion capabilites to an agent. When used with a localizing agent, it matches timestamps aswell
    NOTE: Requires extra arguments passed in somehow and you should always be extending this class, and use partial constructors further up
    NOTE: This means you cannot run this class as is
    """

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.capture: Union[
            Capture, depthCamera, OpenCVCapture, ConfigurableCapture, CaptureWIntrinsics
        ] = kwargs.get("capture", None)
        if self.capture is None:
            raise ValueError("CameraUsingAgentBase requires a capture object")

        self.depthEnabled = issubclass(self.capture.__class__, depthCamera)
        self.isCv2Backend = issubclass(self.capture.__class__, OpenCVCapture)
        self.isConfigurable = issubclass(self.capture.__class__, ConfigurableCapture)
        self.isWIntrinsics = issubclass(self.capture.__class__, CaptureWIntrinsics)

        
        

        self.showFrames: bool = kwargs.get("showFrames", False)
        self.hasIngested: bool = False
        self.exit: bool = False
        self.WINDOWNAMEDEPTH: str = "depth_frame"
        self.WINDOWNAMECOLOR: str = "color_frame"
        self.latestFrameDEPTH: Optional[np.ndarray] = None
        self.latestFrameMain: Optional[np.ndarray] = None
        self.calibActive: bool = False

    def create(self) -> None:
        super().create()
        
        self.capture.create()
        self.__testCapture()

        # the environment might not be able to display frames, even if we want to
        if not canCurrentlyDisplay:
            self.Sentinel.warning("This environment cannot display frames. Showframes will be restricted to False.")
            self.showFrames = False

        # if we are not main thread, even if it says showframe true we cannot allow it
        if not self.isMainThread:
            self.Sentinel.warning(
                "When an agent is not running on the main thread, it cannot display frames directly. Showframes will be restricted to False."
            )
            self.showFrames = False
        
        # named windoows to display
        if self.showFrames:
            cv2.namedWindow(self.WINDOWNAMECOLOR)

            if self.depthEnabled:
                cv2.namedWindow(self.WINDOWNAMEDEPTH)


        frameShape = self.capture.getFrameShape()
        self.__createCalibrationProperties(frameShape)
        self.__createCameraStreamProperties(frameShape)


        self.calibrationUtil = CalibrationUtil(self.capture.getName())
        self.calibration = self.calibrationUtil.getCalibration()

        if self.calibration is not None:
            self.preprocessFrame = lambda frame: self.calibration.undistortFrame(frame)            
        else:
            self.preprocessFrame = lambda frame : frame

        self.__sendInitialUpdate()
        

    def __testCapture(self) -> None:
        """Test if the camera is properly functioning"""
        if self.capture.isOpen():
            frame = self.capture.getMainFrame()
            retTest = frame is not None

            if self.depthEnabled:
                depthFrame = self.capture.getDepthFrame()
                retTest = retTest and depthFrame is not None
        else:
            retTest = False

        if not retTest:
            raise BrokenPipeError(f"Failed to read from camera! {type(self.capture)=}")
        
    def __sendInitialUpdate(self) -> None:
        """Set up initial camera intrinsics properties"""
        self.Sentinel.info(f"\nInitializing Camera Info:\n{self.depthEnabled=}\n{self.isCv2Backend=}" +
                            f"\n{self.isConfigurable}\n{self.isWIntrinsics=}")
        if self.calibration:
            if self.customLoaded:
                self.Sentinel.info("Loaded custom camera calibration!")
            else:
                self.Sentinel.info("Could not find camera calibration")

    def __createCalibrationProperties(self, frameShape : tuple):
        self.calibActive = False
        self.timePerPicture = self.updateOp.createGlobalUpdate(
            self.CALIBTIMEPERPICTURE, default=5, loadIfSaved=False
        )
        self.calibProp = self.updateOp.createGlobalUpdate(
            self.CALIBTOGGLEPOSTFIX, default=False, loadIfSaved=False
        )
        self.calibW = self.updateOp.createGlobalUpdate(
            self.CALIBIDEALSHAPEHPOSTFIX, default=frameShape[1], loadIfSaved=False
        )
        self.calibH = self.updateOp.createGlobalUpdate(
            self.CALIBIDEALSHAPEWPOSTFIX, default=frameShape[0], loadIfSaved=False
        )
        self.calibCount = self.updateOp.createGlobalUpdate(
            self.CALIBIDEALCOUNT, default=self.DEFAULTCALIBCOUNT, loadIfSaved=False
        )
        self.isCharucoCalib = self.updateOp.createGlobalUpdate(
            self.ISCHARUCOCALIB, default=True, loadIfSaved=False
        )

    def __createCameraStreamProperties(self, frameShape : tuple):
        self.streamProxy: StreamProxy = self.getProxy(self.CAMERASTREAMNAME)
        streamPath = self.streamProxy.getStreamPath()

        self.propertyOperator.createCustomReadOnlyProperty(
            "stream.IP", streamPath, addBasePrefix=True, addOperatorPrefix=True
        )

        htow = frameShape[0] / frameShape[1]

        self.streamWidth = self.propertyOperator.createCustomProperty(
            "stream.width",
            320,
            addOperatorPrefix=True,
            loadIfSaved=False,
        )
        self.streamHeight = self.propertyOperator.createCustomProperty(
            "stream.height",
            int(320 * htow),
            addOperatorPrefix=True,
            loadIfSaved=False,
        )
   

    def runPeriodic(self) -> None:
        super().runPeriodic()

        # we show the last frames before ingesting new frames, as this allows the frame to be annotated by any inheritors of this class
        # then since the annottated frames will be shown before being overwritten by the new read, they can be displayed
        self.__showLastFrame()
        self.__ingestFrames()

        if self.calibProp.get() and not self.calibActive:
            self.__initCalibrator()
        
        if self.calibActive and not self.calibrator.isFinished():
            if not self.calibProp.get():
                # premature exit
                self.calibActive = False
            else:                
                # take a picture every N seconds (to allow for moving of the calibration board)
                if time.time() - self.timeSinceLastPicture > self.timePerPicture.get():
                    self.calibrator.savePicture(self.latestFrameMain)

                if self.calibrator.isFinished():
                    self.__finishCalibration()
        

    def __showLastFrame(self):
        if self.hasIngested:
            # local showing of frame
            if self.showFrames:
                cv2.imshow(self.WINDOWNAMECOLOR, self.latestFrameMain)

                if self.latestFrameDEPTH is not None:
                    cv2.imshow(self.WINDOWNAMEDEPTH, self.latestFrameDEPTH)

                if cv2.waitKey(1) & 0xFF == ord("q"):
                    self.exit = True

            # send to mjpeg stream
            # clear if above size
            streamWidthI = int(self.streamWidth.get())
            streamHeightI = int(self.streamHeight.get())
            if (
                streamWidthI != self.latestFrameMain.shape[1]
                or streamHeightI != self.latestFrameMain.shape[0]
            ):
                resizedFrame = cv2.resize(
                    self.latestFrameMain,
                    (streamWidthI, streamHeightI),
                )
                self.streamProxy.put(resizedFrame)
            else:
                self.streamProxy.put(self.latestFrameMain)
    
    def __ingestFrames(self):
        with self.timer.run("cap_read"):
            self.hasIngested = True

            if self.depthEnabled:
                latestFrames = self.capture.getDepthAndColorFrame()
                if latestFrames is None:
                    raise BrokenPipeError("Camera failed to capture with depth!")

                self.latestFrameDEPTH = latestFrames[0]

                self.latestFrameMain = self.preprocessFrame(latestFrames[1])

            else:
                frame = self.capture.getMainFrame()
                if frame is None:
                    raise BrokenPipeError("Camera failed to capture!")

                self.latestFrameMain = self.preprocessFrame(frame)
    
    def __initCalibrator(self):
        self.calibActive = True
        self.timeSinceLastPicture = time.time()
        
        w = self.calibW.get()
        h = self.calibH.get()

        numPics = self.calibCount.get()
        isCharuco = self.isCharucoCalib.get()

        self.Sentinel.info(f"Starting Calibration! Goal Resolution: {w=} {h=} | {numPics=} | {isCharuco=}")
        
        self.calibrator = calibration.Calibrator(
            nFrames=numPics, targetW=w, targetH=h, isCharucoBoard=isCharuco
        )

    def __finishCalibration(self):
        if not self.calibActive:
            raise RuntimeError("Called __finishCalibration when a calibration is not active!")
        
        self.calibActive = False
        outputCalib = self.calibrator.startCalibration()

        if outputCalib is None:
            self.Sentinel.warning("Failed to calibrate camera!")
            return
        
        self.calibrationUtil.setNewCalibration(outputCalib)
        self.preprocessFrame = lambda frame : outputCalib.undistortFrame(frame)    
    
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



