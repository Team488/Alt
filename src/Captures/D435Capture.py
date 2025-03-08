from abstract.depthCamera import depthCamera
from tools.Constants import D435IResolution
from tools.realsense2Helper import realsense2Helper


class D435Capture(depthCamera):
    def __init__(self, res: D435IResolution):
        self.res = res

    def create(self):
        self.realsenseHelper = realsense2Helper(self.res)
        intr = self.realsenseHelper.getCameraIntrinsics()
        super().setIntrinsics(intr)

    def getColorFrame(self):
        return self.realsenseHelper.getDepthAndColor()[1]

    def getFps(self):
        return self.realsenseHelper.getFps()

    def getDepthFrame(self):
        return self.getDepthAndColorFrame()[0]  # linked together

    def getDepthAndColorFrame(self):
        return self.realsenseHelper.getDepthAndColor()

    def isOpen(self):
        return self.realsenseHelper.isOpen()

    def close(self):
        self.realsenseHelper.close()


def startDemo():
    import cv2

    cap = D435Capture(D435IResolution.RS480P)
    cap.create()

    while cap.isOpen():
        depth, color = cap.getDepthAndColorFrame()
        cv2.imshow("depth", depth)
        cv2.imshow("color", color)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.close()
