"""network.py

Utility functions for network-related operations, such as retrieving the device's
hostname and local IP address.

This module provides:
- DEVICEHOSTNAME: The current device's hostname.
- DEVICEIP: The current device's local IP address.
- A function to programmatically determine the local IP address.
"""

from __future__ import annotations

import socket

DEVICEHOSTNAME = socket.gethostname()


def get_local_ip():
    """
    Determines the local IP address of the current device.

    Attempts to connect to a public DNS server (Google's 8.8.8.8) to determine
    the outward-facing local IP address. Falls back to '127.0.0.1' if no network
    connection is available.

    Returns:
        str: The local IP address as a string.
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
