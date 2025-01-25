""" Process to run on orin """

import cv2
import argparse
import logging
import time
import numpy as np
from tools.Constants import CameraIdOffsets
from JXTABLES.XTablesClient import XTablesClient
from JXTABLES import XTableValues_pb2
from coreinterface.DetectionPacket import DetectionPacket
from coreinterface.FramePacket import FramePacket
from coreinterface.MainProcessInterface import MainProcessBase
from mapinternals.CentralProcessor import CentralProcessor
from pathplanning.PathGenerator import PathGenerator
from tools import NtUtils

processName = "Main__Process"
logger = logging.getLogger(processName)

interface = MainProcessBase(XTablesClient())


def mainLoop():
    try:
        while True:
            interface.central_update()
            # put code here....

            # central.map.displayHeatMaps()
            # cv2.waitKey(1)
    except Exception as e:
        print(e)
    finally:
        logger.info("Ending main process")
        cv2.destroyAllWindows()
        return


if __name__ == "__main__":
    mainLoop()
