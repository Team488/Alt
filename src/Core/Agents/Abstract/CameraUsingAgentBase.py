"""
Camera Using Agent Base Module - Base class for agents that process camera frames

This module provides the CameraUsingAgentBase class, which extends the basic Agent
class with camera frame capture and processing capabilities. It handles camera
initialization, frame acquisition, optional preprocessing (such as undistortion),
and frame display/sharing with both local display and network transmission.

Key features:
- Automatic camera initialization and error handling
- Support for both regular and depth cameras
- Camera calibration capabilities for supported camera types
- Frame preprocessing (e.g., undistortion) using loaded calibrations
- Local frame display in OpenCV windows
- Network sharing of frames via the update system
- Intelligent handling of headless environments

Concrete agent implementations that work with camera input should inherit from
this class rather than the basic Agent class to leverage its camera handling
functionality.
"""

import datetime
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
from tools.depthAiHelper import DepthAIHelper
from abstract.depthCamera import depthCamera
from tools import calibration
from Core.ConfigOperator import staticLoad
import Core


class CameraUsingAgentBase(Agent):
    """
    Base class for agents that process camera frames.
    
    This abstract base class extends the basic Agent class with camera frame
    capture and processing capabilities. It handles camera initialization,
    frame acquisition, optional preprocessing (such as undistortion), and
    frame display/sharing. It also provides camera calibration functionality
    for supported camera types.
    
    The inheritance hierarchy is:
    Agent -> CameraUsingAgentBase
    
    Attributes:
        FRAMEPOSTFIX: Suffix for network frame updates
        FRAMETOGGLEPOSTFIX: Suffix for frame sending toggle property
        CALIBTOGGLEPOSTFIX: Suffix for calibration toggle property
        CALIBIDEALSHAPEWPOSTFIX: Suffix for calibration width property
        CALIBIDEALSHAPEHPOSTFIX: Suffix for calibration height property
        CALIBIDEALCOUNT: Property name for calibration frame count
        DEFAULTCALIBCOUNT: Default number of frames for calibration
        CALIBRATIONPREFIX: Prefix for calibration file paths
        capture: Camera capture device interface
        depthEnabled: Whether depth capture is available
        iscv2Configurable: Whether camera supports custom calibration
        preprocessFrame: Optional function to process frames before use
        showFrames: Whether to display frames in windows
        latestFrameMain: Most recent color frame
        latestFrameDEPTH: Most recent depth frame (if available)
        
    Notes:
        - This class should be extended, not used directly
        - Requires a capture object to be passed in constructor
        - When used with a localizing agent, it matches timestamps
    """
    
    # Constants for property names and defaults
    FRAMEPOSTFIX = "Frame"
    FRAMETOGGLEPOSTFIX = "SendFrame"
    CALIBTOGGLEPOSTFIX = "StartCalib"
    CALIBIDEALSHAPEWPOSTFIX = "CALIBGOALSHAPEW"
    CALIBIDEALSHAPEHPOSTFIX = "CALIBGOALSHAPEH"
    CALIBIDEALCOUNT = "NUMCALIBPICTURES"
    DEFAULTCALIBCOUNT = 100
    CALIBRATIONPREFIX = "Calibrations"

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a new CameraUsingAgentBase instance.
        
        Sets up the camera capture device, loads any existing calibration,
        and initializes frame processing capabilities.
        
        Args:
            **kwargs: Keyword arguments which must include:
                - capture: A camera capture device
                - showFrames (optional): Whether to display frames in windows
                
        Raises:
            ValueError: If no capture object is provided
        """
        super().__init__(**kwargs)
        self.capture: Union[
            Capture, depthCamera, ConfigurableCameraCapture
        ] = kwargs.get("capture", None)
        if self.capture is None:
            raise ValueError("CameraUsingAgentBase requires a capture object")
            
        # Determine camera capabilities
        self.depthEnabled: bool = issubclass(self.capture.__class__, depthCamera)
        self.iscv2Configurable: bool = issubclass(
            self.capture.__class__, ConfigurableCameraCapture
        )
        self.customLoaded: bool = False
        self.preprocessFrame: Optional[Callable[[np.ndarray], np.ndarray]] = None
        self.calibMTime: Union[float, str] = "Not_Set"

        if self.iscv2Configurable:
            # Try to load a saved camera calibration
            calibPath = f"{os.path.join(self.CALIBRATIONPREFIX, self.capture.getUniqueCameraIdentifier())}.json"

            out = staticLoad(calibPath)
            if out:
                # Set up frame preprocessing with the loaded calibration
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
            # Set appropriate calibration status for non-configurable cameras
            if self.depthEnabled:
                self.calibMTime = "Prebaked_Internally"
            else:
                self.calibMTime = "Not_Using_Intrinsics"

        # Initialize display and frame variables
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
        """
        Set up initial camera intrinsics properties in the property system.
        
        This method publishes information about the camera's intrinsic parameters
        (focal length, principal point, etc.) and calibration status to the
        property system so that other components can access them.
        
        Raises:
            ValueError: If PropertyOperator is not initialized
        """
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
            
        # Publish calibration timestamp in human-readable format
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
        """
        Initialize the camera and set up frame display/sharing options.
        
        This method:
        1. Initializes the camera capture device
        2. Configures frame display settings based on environment capabilities
        3. Tests the camera to ensure it's functioning
        4. Creates properties for calibration and frame sharing controls
        5. Sets up display windows if frame visualization is enabled
        
        Raises:
            ValueError: If required components are missing
            BrokenPipeError: If camera initialization fails
        """
        super().create()
        # Check if the current environment supports visual display
        if not Core.canCurrentlyDisplay:
            self.Sentinel.warning("This environment cannot display frames!")
            self.showFrames = False

        # Initialize the camera
        self.capture.create()
        self.sendInitialUpdate()

        # Frame display requires the main thread
        if not self.isMainThread:
            if self.Sentinel:
                self.Sentinel.warning(
                    "When an agent is not running on the main thread, it cannot display frames directly."
                )
            self.showFrames = False

        # Test that the camera is working properly
        self.testCapture()

        # Create properties for controlling calibration and frame sharing
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

        # Create display windows if needed
        if self.showFrames:
            cv2.namedWindow(self.WINDOWNAMECOLOR)

            if self.depthEnabled:
                cv2.namedWindow(self.WINDOWNAMEDEPTH)

    def testCapture(self) -> None:
        """
        Test if the camera is properly functioning.
        
        Attempts to open the camera and capture a frame to ensure
        that the camera is working correctly.
        
        Raises:
            BrokenPipeError: If the camera fails to open or return a valid frame
        """
        if self.capture.isOpen():
            frame = self.capture.getMainFrame()
            retTest = frame is not None
        else:
            retTest = False

        if not retTest:
            raise BrokenPipeError(f"Failed to read from camera! {type(self.capture)=}")

    def runPeriodic(self) -> None:
        """
        Execute the agent's periodic processing logic.
        
        This method is called regularly by the agent framework and performs the
        following operations:
        1. Updates local state from property values
        2. Performs camera calibration if requested
        3. Captures new frames from the camera
        4. Preprocesses frames if needed
        5. Displays frames locally if enabled
        6. Sends frames over the network if enabled
        
        The method handles camera failures and ensures proper synchronization
        between the agent state and the property system.
        
        Raises:
            ValueError: If required properties are not initialized
            BrokenPipeError: If camera capture fails
        """
        super().runPeriodic()
        if not hasattr(self, 'sendFrameProp') or not hasattr(self, 'calibProp'):
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
        """
        Clean up resources when the agent is closing.
        
        Closes the camera capture device and destroys any open
        display windows to ensure clean shutdown.
        """
        super().onClose()
        self.capture.close()

        if self.showFrames:
            cv2.destroyAllWindows()

    def isRunning(self) -> bool:
        """
        Check if the agent should continue running.
        
        Verifies that the camera is still available and that the
        agent has not been signaled to exit.
        
        Returns:
            True if the agent should continue running, False otherwise
        """
        if not self.capture.isOpen():
            if self.Sentinel:
                self.Sentinel.fatal("Camera cannot be opened!")
            return False
        if self.exit:
            if self.Sentinel:
                self.Sentinel.info("Gracefully exiting...")
            return False
        return True

    def forceShutdown(self) -> None:
        """
        Handle forced shutdown of the agent.
        
        Ensures the camera is properly closed even during
        abnormal termination of the agent.
        """
        super().forceShutdown()
        self.capture.close()
