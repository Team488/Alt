"""
Captures Package - Camera and sensor data acquisition interfaces

This package provides a collection of classes for acquiring data from various
camera types and other sensors. It abstracts the differences between camera
hardware, file sources, and simulation inputs behind a common interface.

Key components include:
- OAKCapture: Interface for OpenCV AI Kit (OAK-D) cameras
- D435Capture: Interface for Intel RealSense D435 depth cameras
- CameraCapture: Generic configurable camera interface
- FileCapture: Interface for reading from video files
- Utilities for camera configuration and frame processing

All capture classes implement a common interface defined in the abstract.Capture
module, allowing the rest of the system to work with different data sources
in a unified way.
"""

from .OAKCapture import OAKCapture
from .D435Capture import D435Capture
from .CameraCapture import ConfigurableCameraCapture
from .FileCapture import FileCapture
