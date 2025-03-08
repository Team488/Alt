from abstract.depthCamera import depthCamera
from tools.Constants import OAKDLITEResolution
from tools.depthAiHelper import DepthAIHelper


class OAKCapture(depthCamera):
    def __init__(self, res: OAKDLITEResolution):
        self.res = res

    def create(self):
        self.depthAiHelper = DepthAIHelper(self.res)
        super().setIntrinsics(self.depthAiHelper.getColorIntrinsics())

    def getDepthAndColorFrame(self):
        return (self.depthAiHelper.getDepthFrame(), self.depthAiHelper.getColorFrame())

    def getDepthFrame(self):
        return self.depthAiHelper.getDepthFrame()

    def getColorFrame(self):
        return self.depthAiHelper.getColorFrame()

    def isOpen(self):
        return self.depthAiHelper.isOpen()

    def close(self):
        self.depthAiHelper.close()


def startDemo():
    import cv2

    cap = OAKCapture(OAKDLITEResolution.OAK1080P)
    cap.create()

    while cap.isOpen():
        depth, color = cap.getDepthAndColorFrame()
        cv2.imshow("depth", depth)
        cv2.imshow("color", color)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.close()
