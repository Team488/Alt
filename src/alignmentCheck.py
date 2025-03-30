from Core.Agents.Partials.AlignmentProviderAgent import partialAlignmentCheck
from tools.Constants import SimulationEndpoints
from Alignment.ReefPostAlignmentProvider import ReefPostAlignmentProvider
from Core.Neo import Neo

if __name__ == "__main__":
    alignmentCheckReefLeft = partialAlignmentCheck(
        alignmentProvider=ReefPostAlignmentProvider(),
        cameraPath=SimulationEndpoints.FRONTLEFTSIM.path,
        showFrames=True,
        flushCamMs=50,
    )

    alignmentCheckReefRight = partialAlignmentCheck(
        alignmentProvider=ReefPostAlignmentProvider(),
        cameraPath=SimulationEndpoints.FRONTRIGHTSIM.path,
        showFrames=True,
        flushCamMs=50,
    )

    n = Neo()

    n.wakeAgent(alignmentCheckReefLeft, isMainThread=False)
    n.wakeAgent(alignmentCheckReefRight, isMainThread=False)

    n.waitForAgentsFinished()

    n.shutDown()
