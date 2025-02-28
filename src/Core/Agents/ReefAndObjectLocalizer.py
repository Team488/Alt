from functools import partial
from Core.Agents.Abstract.ObjectLocalizingAgentBase import ObjectLocalizingAgentBase
from Core.Agents.Abstract.ReefTrackingAgentBase import ReefTrackingAgentBase
from tools.Constants import CameraIntrinsics, CameraExtrinsics, InferenceMode


class ReefAndObjectLocalizer(ObjectLocalizingAgentBase, ReefTrackingAgentBase):
    """Agent -> LocalizingAgentBase -> (ObjectLocalizingAgentBase, ReefTrackingAgentBase) -> ReefAndObjectLocalizer"""

    def __init__(
        self,
        cameraPath: str,
        showFrames: bool,
        cameraIntrinsics: CameraIntrinsics,
        cameraExtrinsics: CameraExtrinsics,
        inferenceMode: InferenceMode,
    ) -> None:
        super().__init__(
            cameraPath=cameraPath,
            cameraIntrinsics=cameraIntrinsics,
            cameraExtrinsics=cameraExtrinsics,
            inferenceMode=inferenceMode,
            showFrames=showFrames,
        )  # heres where we add our constants


def ReefAndObjectLocalizerPartial(
    cameraPath: str,
    cameraIntrinsics: CameraIntrinsics,
    cameraExtrinsics: CameraExtrinsics,
    inferenceMode: InferenceMode,
    showFrames: bool = False,
):
    return partial(
        ReefAndObjectLocalizer,
        cameraPath=cameraPath,
        showFrames=showFrames,
        cameraIntrinsics=cameraIntrinsics,
        cameraExtrinsics=cameraExtrinsics,
        inferenceMode=inferenceMode,
    )
