import cv2
from JXTABLES.XTablesClient import XTablesClient
from coreinterface.FramePacket import FramePacket

client = XTablesClient(debug_mode=True)

while True:
    framepkt = client.getBytes("Adem-GamingPc.Frame")
    if framepkt is not None:
        framepkt = FramePacket.fromBytes(framepkt)
        cv2.imshow("frame", FramePacket.getFrame(framepkt))
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
