from JXTABLES.TempConnectionManager import TempConnectionManager as tcm
from Captures import FileCapture
from Core.Agents.Partials.VideoWriterAgent import partialVideoWriterAgent
from Alignment.ReefPostAlignmentProvider import ReefPostAlignmentProvider
from Core.Agents.Partials.AlignmentProviderAgent import partialAlignmentCheck
from Core.Neo import Neo
from Core.Agents import OrangePiAgent

alignment = partialAlignmentCheck(
    alignmentProvider=ReefPostAlignmentProvider(), showFrames=False,cameraPath="/dev/color_camera"
)

# agent = partialVideoWriterAgent(capture=FileCapture(videoFilePath="/dev/color_camera"),savePath="StingerCam.mp4")


tcm.invalidate()

if __name__ == "__main__":
    n = Neo()
    n.wakeAgent(alignment, isMainThread=True)
    n.shutDown()
