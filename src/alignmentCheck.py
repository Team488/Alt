from Core.Agents.Partials.AlignmentProviderAgent import (
    partialAlignmentCheck
)
from Alignment.ReefPostAlignmentProvider import ReefPostAlignmentProvider
from Core.Neo import Neo

if __name__ == "__main__":
    alignmentCheckReef = partialAlignmentCheck(
        alignmentProvider=ReefPostAlignmentProvider(),
        cameraPath=0,
        showFrames=True,
    )




    n = Neo()

    n.wakeAgent(alignmentCheckReef, isMainThread=True)
    n.shutDown()