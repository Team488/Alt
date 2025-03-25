"""
Centralized Tracking Package - Multi-camera object tracking and fusion

This package implements a centralized tracking system that combines detections
from multiple cameras to maintain consistent object tracks. It handles the
challenges of fusing observations across different viewpoints and managing
object identities over time.

Key capabilities include:
- Tracking objects across multiple camera views
- Maintaining consistent object IDs through occlusions and view changes
- Fusing position estimates for improved accuracy
- Managing conflicting detections from different cameras
- Providing a unified tracking interface for the rest of the system

The centralized tracking approach improves robustness by leveraging multiple
perspectives and reduces the impact of individual camera failures or occlusions.
"""