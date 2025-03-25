"""
Reef Tracking Package - Underwater reef element detection and positioning

This package provides functionality for detecting, tracking, and localizing reef
elements in underwater environments. It processes camera input to identify coral,
algae, AprilTags, and other reef-related features.

Key components include:
- Reef state representation and management
- AprilTag detection and identification for precise positioning
- Color-based histogram matching for coral and algae detection
- Pose solving to determine 3D positions from 2D detections
- Visualization tools for reef tracking data
- Integration with network communication for dashboard displays

The reef tracking system is crucial for the robot's ability to interact with and
navigate around the underwater reef environment, providing accurate positional
information for path planning and task execution.
"""