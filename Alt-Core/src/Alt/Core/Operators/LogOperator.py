"""LogOperator.py

Provides logging utilities for the application, including creation of loggers,
setting log levels, and managing a central logger instance.

Functions:
    createLogger: Creates a logger with a unique name and file handler.
    setMainLogger: Sets the main logger instance.
    createAndSetMain: Creates and sets the main logger.
    setLogLevel: Sets the log level for the central logger.
    getChildLogger: Gets a child logger derived from the central logger.
"""

import os
import socket
import logging
from typing import Union, Final

BASELOGDIR = os.path.join(os.path.expanduser("~"), ".ALTLOGS")
os.makedirs(BASELOGDIR, exist_ok=True)


LOGLEVEL = logging.DEBUG

# Use hostname as a unique identifier for this instance
UniqueId: Final[str] = socket.gethostname()


def createLogger(loggerName: str):
    """
    Create a logger with a unique name and file handler.

    Args:
        loggerName (str): The name of the logger.

    Returns:
        logging.Logger: The created logger instance.
    """
    from ..Utils.timeFmt import getTimeStr

    fullName = f"{loggerName}[{UniqueId}]"
    logger = logging.getLogger(fullName)
    logger.setLevel(LOGLEVEL)

    if not logger.handlers:
        log_filename = os.path.join(
            BASELOGDIR, f"{fullName}_{getTimeStr()}.log"
        )
        file_handler = logging.FileHandler(log_filename, mode="a", encoding="utf-8")
        file_handler.setFormatter(
            logging.Formatter(
                "%(asctime)s - %(processName)s - %(levelname)s - %(message)s"
            )
        )
        logger.addHandler(file_handler)

    return logger

def setMainLogger(mainLogger: logging.Logger):
    """
    Set the main logger instance.

    Args:
        mainLogger (logging.Logger): The logger to set as the main logger.
    """
    global Sentinel
    Sentinel = mainLogger

def createAndSetMain(loggerName: str):
    """
    Create and set the main logger using the given name.

    Args:
        loggerName (str): The name for the main logger.
    """
    setMainLogger(createLogger(loggerName))

Sentinel = createLogger("Core")


def setLogLevel(level: Union[int, str]) -> None:
    """
    Set the log level for the central logger.

    Args:
        level (int or str): Logging level (can be an integer level or a string name).
    """
    Sentinel.setLevel(level)


def getChildLogger(name: str) -> logging.Logger:
    """
    Get a child logger derived from the central logger.

    Args:
        name (str): Name for the child logger.

    Returns:
        logging.Logger: A Logger instance with the given name as a child of the central logger.
    """
    return Sentinel.getChild(name)
