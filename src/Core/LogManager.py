import socket
import logging

UniqueId = socket.gethostname()
Sentinel = logging.getLogger(f"Core[{UniqueId}]")
Sentinel.setLevel(level=logging.CRITICAL)

def setLogLevel(level):
    Sentinel.setLevel(level)

def getLogger(name):
    return Sentinel.getChild(name)