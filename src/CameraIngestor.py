"""
Camera Ingestor Module - Simple script to display camera frames.

This module creates a Neo instance and runs the FrameDisplayer agent on the main thread.
It serves as a minimal example of how to use the Neo system to ingest and display
camera frames. After running the FrameDisplayer, it properly shuts down the Neo system.

Usage:
    python CameraIngestor.py
"""

from Core.Neo import Neo
from Core.Agents import FrameDisplayer

# Create a Neo instance to manage the system
n = Neo()

# Wake the FrameDisplayer agent on the main thread
# This will display camera frames until the user closes the display
n.wakeAgent(FrameDisplayer, isMainThread=True)

# Properly shut down the Neo system when finished
n.shutDown()
