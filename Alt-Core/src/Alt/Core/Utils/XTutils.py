"""XTutils.py

Utility functions for converting paths to XTables coordinate format.

This module provides:
- A function to convert a sequence of points into a list of XTableValues_pb2.Coordinate objects.
"""

from __future__ import annotations

from typing import List, Sequence, Union, Tuple
from JXTABLES import XTableValues_pb2


def getCoordinatesAXCoords(
    path: Sequence[Sequence[float]],
) -> List[XTableValues_pb2.Coordinate]:
    """
    Converts a path into XTables coordinate format.

    Args:
        path (Sequence[Sequence[float]]): A sequence of points, where each point is a sequence of at least 2 floats (x, y).
            Points can be represented as lists or tuples.

    Returns:
        List[XTableValues_pb2.Coordinate]: A list of XTableValues_pb2.Coordinate objects.

    Notes:
        - Path units are assumed to be in centimeters.
        - Output coordinates are converted to meters (divided by 100).
    """
    coordinates: List[XTableValues_pb2.Coordinate] = []
    for waypoint in path:
        element = XTableValues_pb2.Coordinate(x=waypoint[0] / 100, y=waypoint[1] / 100)
        coordinates.append(element)
    return coordinates
