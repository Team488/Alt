import subprocess
from tools.Constants import InferenceMode
from .LogManager import getLogger
import sys

COREMODELTABLE = "MainProcessInferenceMODE"
COREINFERENCEMODE = InferenceMode.ALCOROBEST2025

def isHeadless():
    try:
        result = subprocess.run(
            [sys.executable, "-c", "import cv2; cv2.namedWindow('test'); cv2.destroyWindow('test')"],
            capture_output=True,
            text=True
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