from functools import partial
from Core.Agents.Abstract.ObjectLocalizingAgentBase import ObjectLocalizingAgentBase
from Core.Agents.Abstract.ReefTrackingAgentBase import ReefTrackingAgentBase
from abstract.Capture import ConfigurableCapture
from tools.Constants import CameraExtrinsics, InferenceMode, MapConstants


class ReefAndObjectLocalizer(ObjectLocalizingAgentBase, ReefTrackingAgentBase):
    """Agent -> LocalizingAgentBase -> (ObjectLocalizingAgentBase, ReefTrackingAgentBase) -> ReefAndObjectLocalizer"""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.robotPose2dCMRAD = (
            MapConstants.fieldWidth.getCM() // 1,
            MapConstants.fieldHeight.getCM() // 2,
            0,
        )


def ReefAndObjectLocalizerPartial(
    capture: ConfigurableCapture,
    cameraExtrinsics: CameraExtrinsics,
    inferenceMode: InferenceMode,
    showFrames: bool = False,
):
    return partial(
        ReefAndObjectLocalizer,
        capture=capture,
        showFrames=showFrames,
        cameraIntrinsics=capture.getIntrinsics(),
        cameraExtrinsics=cameraExtrinsics,
        inferenceMode=inferenceMode,
    )
