import socket
import logging
from typing import Union, Optional

UniqueId = socket.gethostname()
Sentinel = logging.getLogger(f"Core[{UniqueId}]")
Sentinel.setLevel(level=logging.DEBUG)


def setLogLevel(level: Union[int, str]) -> None:
    Sentinel.setLevel(level)


def getLogger(name: str) -> logging.Logger:
    return Sentinel.getChild(name)
