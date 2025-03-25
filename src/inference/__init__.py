"""
Inference Package - Machine learning model execution for object detection

This package provides a unified interface for running different types of object
detection models across various hardware backends. It abstracts away the details
of model loading, preprocessing, inference, and result interpretation.

Key components include:
- MultiInferencer: A unified interface for managing multiple inference backends
- Backend-specific implementations for:
  - TensorRT: High-performance NVIDIA GPU acceleration
  - ONNX: Open Neural Network Exchange format runtime
  - RKNN: Rockchip Neural Network acceleration
  - Ultralytics: PyTorch-based YOLOv5/v8/v11 models
- Common utilities for preprocessing images and postprocessing results
- Letterboxing and other operations to prepare images for inference
- Result parsing and normalization for consistent output formats

The inference system supports multiple YOLO model versions (v5, v8, v11) and
can dynamically select the most appropriate backend based on available hardware
and performance requirements.
"""