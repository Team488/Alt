import struct
from typing import Tuple

def getPose2dFromBytes(bytes: bytes) -> Tuple[float, float, float]:
    """
    Unpacks a 2D pose from bytes
    
    Args:
        bytes: Binary data containing 3 double-precision floats
        
    Returns:
        A tuple (x, y, rotation) where units depend on what was packed
    """
    return struct.unpack('ddd', bytes)

def getTranslation3dFromBytes(bytes: bytes) -> Tuple[Tuple[float, float, float], Tuple[float, float, float, float]]:
    """
    Unpacks a 3D pose (translation and rotation) from bytes
    
    Args:
        bytes: Binary data containing 7 double-precision floats
        
    Returns:
        A tuple containing:
            - translation as (x, y, z)
            - rotation as quaternion (w, x, y, z)
    """
    ret = struct.unpack('ddddddd', bytes)
    translation = ret[:3]
    rotation = ret[3:]
    return (translation, rotation)
