"""
Attributes:
    getChildLogger (callable): Provides a logger instance derivied from the central logger.
    staticLoad (callable): Load a saved file.
    DEVICEHOSTNAME (str): The hostname of the current device.
    DEVICEIP (str): The IP address of the current device, determined at runtime.
"""

import socket
from .Operators import LogOperator, ConfigOperator
from .Neo import Neo

getChildLogger = LogOperator.getChildLogger
staticLoad = ConfigOperator.staticLoad

DEVICEHOSTNAME = socket.gethostname()


def get_local_ip():
    """
    Determines the local IP address of the current device using a dummy UDP connection.

    This function attempts to obtain the primary IPv4 address by connecting to a well-known external server
    (Google DNS, 8.8.8.8). If the connection fails, the function defaults to '127.0.0.1' (localhost).

    Returns:
        str: The local IP address of the device. Defaults to '127.0.0.1' if the address cannot be determined.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(("8.8.8.8", 80))  # Google DNS
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"  # Fallback to localhost if no connection is possible
    finally:
        s.close()
    return ip


DEVICEIP = get_local_ip()



