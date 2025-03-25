"""
Localization Module - Object detection and localization system.

This module provides a simple interface to run the object localization system
with a RealSense D435 camera. It initializes the necessary components and runs
the ObjectLocalizingAgent on the main thread.

The localization system detects objects (algae, coral, robots) in the camera
feed using the specified inference model and displays the results in real-time.

Usage:
    python localization.py
"""

from Core.Agents.Abstract.ObjectLocalizingAgentBase import ObjectLocalizingAgentPartial
from Core.Neo import Neo
from tools.Constants import (
    InferenceMode,
    ColorCameraExtrinsics2024,
    CameraIntrinsicsPredefined,
    D435IResolution,
    CommonVideos,
)
from Captures import D435Capture, FileCapture, ConfigurableCameraCapture

# Create an ObjectLocalizingAgent with:
# - D435 RealSense camera at 640x480 resolution
# - No camera extrinsics (camera at origin)
# - Using the best ALCORO model for 2025 (detects algae, coral, robots)
# - Display frames in a window (showFrames=True)
agent = ObjectLocalizingAgentPartial(
    D435Capture(D435IResolution.RS480P),
    ColorCameraExtrinsics2024.NONE,
    InferenceMode.ALCOROBEST2025,
    showFrames=True,
)

# Initialize the Neo system
n = Neo()

# Run the localization agent on the main thread
# This will display the camera feed with object detection boxes
n.wakeAgent(agent, isMainThread=True)
