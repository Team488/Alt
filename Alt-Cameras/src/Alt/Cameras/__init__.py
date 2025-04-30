from .Captures.OAKCapture import OAKCapture
from .Captures.D435Capture import D435Capture
from .Captures.OpenCVCapture import OpenCVCapture



def isHeadlessDisplay():
    import subprocess
    import sys

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


canCurrentlyDisplay = not isHeadlessDisplay()

