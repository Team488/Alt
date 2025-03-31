from Core.Agents.Partials.AlignmentProviderAgent import partialAlignmentCheck
from tools.Constants import SimulationEndpoints, CommonVideos
from Alignment.ReefPostAlignmentProvider import ReefPostAlignmentProvider
from Core.Neo import Neo

if __name__ == "__main__":
    alignmentCheckReefLeft = partialAlignmentCheck(
        alignmentProvider=ReefPostAlignmentProvider(),
        cameraPath=SimulationEndpoints.FRONTRIGHTSIM.path,
        showFrames=True,
        flushCamMs=50,
    )

    n = Neo()

    n.wakeAgent(alignmentCheckReefLeft, isMainThread=True)

    n.waitForAgentsFinished()

    n.shutDown()
