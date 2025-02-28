import socket
import logging

UniqueId = socket.gethostname()
Sentinel = logging.getLogger(f"Core[{UniqueId}]")
Sentinel.setLevel(level=logging.DEBUG)


def setLogLevel(level) -> None:
    Sentinel.setLevel(level)


def getLogger(name):
    return Sentinel.getChild(name)
