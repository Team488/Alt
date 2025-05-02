from Alt.Core import getChildLogger
from Alt.Core.Constants.Field import Field

from ..Estimation.UKF import Ukf
from ..Estimation.KalmanLabeler import KalmanLabeler
from ..Estimation.KalmanCache import KalmanCache
from ..inference.ModelConfig import ModelConfig
from ..Localization.LocalizationResult import DeviceLocalizationResult
from .probmap import ProbMap

Sentinel = getChildLogger("Localization_Pipeline_Step2")


class PipelineStep2:
    def __init__(
        self,
        modelConfig: ModelConfig,
        field: Field,
    ) -> None:
        self.modelConfig = modelConfig
        self.objects = self.modelConfig.getObjects()
        self.nClasses = len(self.objects)

        self.kalmanCaches = [KalmanCache() for _ in range(self.nClasses)]
        self.objectmap = ProbMap(self.objects, field.getWidth(), field.getHeight())
        self.ukf = Ukf(field)
        self.labler = KalmanLabeler(self.kalmanCaches, self.nClasses)
        

    def processFrameUpdate(
        self,
        deviceResults: list[DeviceLocalizationResult],
        timeStepMs,
    ) -> None:
        # dissipate at start of iteration
        self.objectmap.disspateOverTime(timeStepMs)

        # go through each detection and do the magic
        for deviceResult in deviceResults:
            


            self.labler.updateRealIds(deviceResult.localizedResults, offset, timeStepMs)
            # todo add feature deduping here

            for localizationResult in deviceResult.localizedResults:
                # first load in to ukf, (if completely new ukf will load in as new state)
                # index will be filtered out by labler
                if localizationResult.class_idx < 0 or localizationResult.class_idx >= self.nClasses:
                    Sentinel.warning("Out of bounds class id in pipeline")

                x, y = localizationResult.location.x, localizationResult.location.y

                self.kalmanCaches[localizationResult.class_idx].LoadInKalmanData(localizationResult.deepsort_id, x, y, self.ukf)

                newState = self.ukf.predict_and_update([x, y])

                # now we have filtered data, so lets store it. First thing we do is cache the new ukf data
                self.kalmanCaches[localizationResult.class_idx].saveKalmanData(localizationResult.deepsort_id, self.ukf)

                # input new estimated state into the map
                self.objectmap.addDetectedObject(
                    localizationResult.class_idx, int(newState[0]), int(newState[1]), localizationResult.conf  
                )
