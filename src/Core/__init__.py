"""
Core Package - Central coordination and operational infrastructure

This package contains the core coordination and infrastructure components that
power the robot's software system. It includes operators that manage various
aspects of the system's functionality:

- Central: The primary coordination point for all system components
- Operators: Specialized controllers for properties, configurations, timing, etc.
- Agents: Components that perform specific operational tasks
- Orders: Task definitions that can be dispatched to agents

The Core package establishes a framework where specialized components communicate
through well-defined channels, allowing for a flexible, extensible, and
maintainable system architecture.
"""

import subprocess
from tools.Constants import InferenceMode
from .LogManager import getLogger
import sys

# Constants for inference model configuration
COREMODELTABLE = "MainProcessInferenceMODE"
COREINFERENCEMODE = InferenceMode.ALCOROBEST2025

def isHeadless() -> bool:
    """
    Determine if the system is running in a headless environment without GUI capabilities.
    
    This function tests whether OpenCV can create and destroy a window, which
    requires a working GUI environment. If this fails, we assume the system is
    running headless (e.g., on a server or embedded system without a display).
    
    Returns:
        bool: True if running in headless mode, False if GUI capabilities are available
    """
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import cv2; cv2.namedWindow('test'); cv2.destroyWindow('test')"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            return False  # GUI works
        else:
            print("Qt error detected:", result.stderr)
            return True  # Headless mode
    except Exception as e:
        print("Subprocess failed:", str(e))
        return True  # Assume headless if subprocess crashes    
    
# Global flag indicating whether the system can display visual output
canCurrentlyDisplay = not isHeadless()