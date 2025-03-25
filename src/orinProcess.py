"""
Orin Process Module - Main control script for Orin hardware.

This module manages the main process running on NVIDIA Jetson Orin hardware.
It initializes the Neo system, starts the necessary agents for path planning
and video recording, and launches the Fast Marching Method RPC server for
path planning services.

The script runs several agents in parallel and uses the FastMarchingMethod
RPC service to provide path planning capabilities to other components 
of the system.

Usage:
    python orinProcess.py
"""

from Core.Neo import Neo
from Core.Agents.PathToNearestCoralStation import PathToNearestCoralStation
from Core.Agents.orinIngestorAgent import orinIngestorAgent
from Core.Agents.orinIngestorAgent import getTimeStr
from Core.Agents.VideoWriterAgent import partialVideoWriterAgent
from Captures import FileCapture

# Initialize the Neo system
n = Neo()

# Start the PathToNearestCoralStation agent in a background thread
# This agent finds paths to the nearest coral station
n.wakeAgent(PathToNearestCoralStation, isMainThread=False)

# Start the VideoWriterAgent to record camera feed with timestamp in filename
# Using camera 0 as the capture source
n.wakeAgent(
    partialVideoWriterAgent(FileCapture(0), savePath=f"orinCam_{getTimeStr()}.mp4"),
    isMainThread=False,
)

# Import and start the Fast Marching Method RPC server
# This provides path planning services via RPC
from pathplanning.nmc import fastMarchingMethodRPC
fastMarchingMethodRPC.serve()

# Note: Commented out agents can be uncommented as needed
# n.wakeAgent(CentralAgent, isMainThread=False)
# n.wakeAgent(orinIngestorAgent, isMainThread=False)
