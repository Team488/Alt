import numpy as np
from Alt.Core.Units.Poses import Transform3d

class LocalizationResult:
    def __init__(self, location : Transform3d, class_idx : int, conf : float, deepsort_id : int, features : np.ndarray):
        self.location = location
        self.class_idx = class_idx
        self.conf = conf 
        self.deepsort_id = deepsort_id
        self.features = features


class DeviceLocalizationResult:
    def __init__(self, localizedResults : list[LocalizationResult], deviceUniqueName : str):
        self.localizedResults = localizedResults
        self.deviceUniqueName = deviceUniqueName
    