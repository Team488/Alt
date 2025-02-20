import cv2
from Core.Agents.Abstract.CameraUsingAgentBase import CameraUsingAgentBase
from Core.Agents.Abstract.PositionLocalizingAgentBase import PositionLocalizingAgentBase

class TimestampRegulatedAgentBase(CameraUsingAgentBase, PositionLocalizingAgentBase):
    """Agent -> (CameraUsingAgentBase, PositionLocalizingAgentBase) -> TimestampRegulatedAgentBase

    Using both a camera agent, and a position localizing agent, this agent adds the ability to synchronize timestamps to a give precision using a binned map. Possible todo, add a queue for a max size
    NOTE: this class should always be extended
    """


    def __init__(
        self, cameraPath, showFrames,  binsize = 5 # whatever the timestamp units are in, likely MS but todo figure out
    ):
        super().__init__(cameraPath, showFrames)
        self.binnedMap = {}
        self.binSize = binsize

    def runPeriodic(self):
        super().runPeriodic()
        """Put binning code here TODO"""
