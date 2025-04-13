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
    from ...Common.timeFmt import getTimeStr

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
    global Sentinel
    Sentinel = mainLogger


def createAndSetMain(loggerName: str):
    setMainLogger(createLogger(loggerName))


# create and set inital logger
def initMainLogger():
    createAndSetMain(f"Core")


initMainLogger()


def setLogLevel(level: Union[int, str]) -> None:
    """
    Set the log level for the central logger

    Args:
        level: Logging level (can be an integer level or a string name)
    """
    Sentinel.setLevel(level)


def getChildLogger(name: str) -> logging.Logger:
    """
    Get a child logger derived from the central logger

    Args:
        name: Name for the child logger

    Returns:
        A Logger instance with the given name as a child of the central logger
    """
    return Sentinel.getChild(name)
