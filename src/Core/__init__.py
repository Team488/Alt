import socket
import subprocess
import tools.Constants
import sys
from Core.LogManager import getChildLogger


COREMODELTABLE = "MainProcessInferenceMODE"
COREINFERENCEMODE = tools.Constants.InferenceMode.ALCOROBEST2025
DEVICEHOSTNAME = socket.gethostname()


def get_local_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.settimeout(0)
    try:
        s.connect(("8.8.8.8", 80))  # Google DNS
        ip = s.getsockname()[0]
    except Exception:
        ip = "127.0.0.1"  # Fallback if no connection is possible
    finally:
        s.close()
    return ip


DEVICEIP = get_local_ip()


def isHeadless():
    try:
        result = subprocess.run(
            [
                sys.executable,
                "-c",
                "import cv2; cv2.namedWindow('test'); cv2.destroyWindow('test')",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            return False  # GUI works
        else:
            print("Qt error detected:", result.stderr)
            return True  # Headless mode
    except Exception as e:
        print("Subprocess failed:", str(e))
        return True  # Assume headless if subprocess crashes


canCurrentlyDisplay = not isHeadless()
