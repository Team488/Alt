import socket
import logging
from typing import Union, Optional, Final

# Use hostname as a unique identifier for this instance
UniqueId: Final[str] = socket.gethostname()

# Central logger instance for the entire application
Sentinel: Final[logging.Logger] = logging.getLogger(f"Core[{UniqueId}]")
Sentinel.setLevel(level=logging.DEBUG)


def setLogLevel(level: Union[int, str]) -> None:
    """
    Set the log level for the central logger
    
    Args:
        level: Logging level (can be an integer level or a string name)
    """
    Sentinel.setLevel(level)


def getLogger(name: str) -> logging.Logger:
    """
    Get a child logger derived from the central logger
    
    Args:
        name: Name for the child logger
        
    Returns:
        A Logger instance with the given name as a child of the central logger
    """
    return Sentinel.getChild(name)
