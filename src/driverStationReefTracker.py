# from JXTABLES.TempConnectionManager import TempConnectionManager as tcm
# from Core.Neo import Neo
# from Core.Agents import InferenceAgent, DriveToTargetAgent, OrangePiAgent
# from Core.Orders import OrderExample

# # removes the temp ip for testing in main
# tcm.invalidate()

# n = Neo()
# n.wakeAgent(DriveToTargetAgent, isMainThread=True)
# n.waitForAgentsFinished()
# n.shutDown()
import time

import cv2
from tools.Constants import (
    CameraIntrinsics,
    CameraIntrinsicsPredefined,
    ColorCameraExtrinsics2024,
    ATCameraExtrinsics2025,
)
from reefTracking.reefTracker import ReefTracker

# intr = CameraIntrinsics.fromCustomConfig("assets/bigboycalib.json")
intr = CameraIntrinsicsPredefined.OAKDLITE1080P

est = ReefTracker(intr, isDriverStation=True)

cap = cv2.VideoCapture(0)
CameraIntrinsics.setCapRes(intr, cap)
from tools.depthAiHelper import DepthAIHelper

helper = DepthAIHelper()

while True:
    frame = helper.getFrame()
    print(est.getAllTracks(frame, drawBoxes=True))
    cv2.imshow("RGB Camera", frame)

    if cv2.waitKey(1) == ord("q"):
        break

cv2.destroyAllWindows()
