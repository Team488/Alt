import time
from JXTABLES.XTablesClient import XTablesClient
import cv2
from coreinterface.FramePacket import FramePacket

client = XTablesClient(ip="192.168.0.17")
def handle_update(ret):
    frame = FramePacket.fromBytes(ret.value)
    cv2.imshow(frame.message,FramePacket.getFrame(frame))
    cv2.waitKey(1)

client.subscribe("REARRIGHT",consumer=handle_update)

while True:
    time.sleep(0.01)
    pass