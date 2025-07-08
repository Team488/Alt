"""NtUtils.py

Utility functions for unpacking pose and translation data from bytes, typically used
for network transmission or binary storage of pose information.

This module provides:
- Functions to unpack 2D and 3D pose data from byte sequences.
"""

from __future__ import annotations

import struct
from typing import Tuple


def getPose2dFromBytes(bytes: bytes) -> Tuple[float, float, float]:
    """
    Unpacks a 2D pose from a bytes object.

    Args:
        bytes (bytes): Binary data containing 3 double-precision floats (x, y, rotation).

    Returns:
        Tuple[float, float, float]: A tuple (x, y, rotation) where units depend on what was packed.
    """
    return struct.unpack("ddd", bytes)


def getTranslation3dFromBytes(
    bytes: bytes,
) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
    """
    Unpacks a 3D pose (translation and rotation) from a bytes object.

    Args:
        bytes (bytes): Binary data containing 7 double-precision floats.

    Returns:
        Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
            A tuple containing:
                - translation as (x, y, z)
                - rotation as quaternion (w, x, y, z)
    """
    ret = struct.unpack("ddddddd", bytes)
    translation = ret[:3]
    rotation = ret[3:]
    return (translation, rotation)
