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
    CameraIntrinsicsPredefined,
    ColorCameraExtrinsics2024,
    ATCameraExtrinsics2025,
)
from reefTracking.reefPostEstimator import ReefPostEstimator

est = ReefPostEstimator(CameraIntrinsicsPredefined.OV9782COLOR, isDriverStation=True)

cap = cv2.VideoCapture(0)

while cap.isOpened():
    ret, frame = cap.read()

    if not ret:
        break

    print(est.estimatePosts(frame, drawBoxes=True))

    cv2.imshow("est", frame)

    if cv2.waitKey(1) & 0xFF == ord("q"):
        break
