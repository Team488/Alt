import socket
import logging
logging.basicConfig

UniqueId = socket.gethostname()
Sentinel = logging.getLogger(f"Core[{UniqueId}]")
Sentinel.setLevel(level=logging.WARNING)


def setLogLevel(level):
    Sentinel.setLevel(level)


def getLogger(name):
    return Sentinel.getChild(name)
