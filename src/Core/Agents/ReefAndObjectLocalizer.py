from functools import partial
from Core.Agents.Abstract.ObjectLocalizingAgentBase import ObjectLocalizingAgentBase
from Core.Agents.Abstract.ReefTrackingAgentBase import ReefTrackingAgentBase
from abstract.Capture import ConfigurableCapture
from tools.Constants import CameraExtrinsics, InferenceMode


class ReefAndObjectLocalizer(ObjectLocalizingAgentBase, ReefTrackingAgentBase):
    """Agent -> LocalizingAgentBase -> (ObjectLocalizingAgentBase, ReefTrackingAgentBase) -> ReefAndObjectLocalizer"""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)


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
