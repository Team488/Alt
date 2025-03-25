"""
Map Internals Package - State estimation and object tracking algorithms

This package provides the core algorithms and data structures for maintaining
probability maps, tracking objects, and estimating states over time. It implements
various filtering and estimation techniques for robust object tracking.

Key components include:
- Probability maps for representing object locations with uncertainty
- Kalman filters for state estimation and tracking
- Unscented Kalman Filters (UKF) for nonlinear state estimation
- Particle filters for complex, non-Gaussian state estimation
- Deep SORT integration for consistent object ID assignment
- Local frame processing for coordinate transformations
- Caching mechanisms for efficient state retrieval

The map internals provide the probabilistic foundation for the system's
understanding of the world, enabling it to reason about object locations
and movements even with noisy sensor data and occlusions.
"""