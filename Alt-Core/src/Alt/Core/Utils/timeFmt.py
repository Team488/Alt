"""timeFmt.py

Utility function for formatting time as a string in a consistent format.

This module provides:
- A function to get the current time or a given time as a formatted string.
"""

from time import localtime, strftime


def getTimeStr(time = None):
    """
    Returns a formatted time string.

    Args:
        time (optional): A time tuple as returned by time.localtime(). If None, uses the current local time.

    Returns:
        str: The formatted time string in the format "YYYY-MM-DD_HH-MM-SS".
    """
    if time is None:
        return strftime("%Y-%m-%d_%H-%M-%S", localtime())
    return strftime("%Y-%m-%d_%H-%M-%S", time)
