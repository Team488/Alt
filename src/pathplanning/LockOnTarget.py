from mapinternals.probmap import ProbMap


class LockOnTarget:
    def __init__(self, map: ProbMap):
        self.map = map
        self.target = None

    """Target must be provided as a (x,y) coordinate in the map"""

    def keep_lock(self, target, min_threshold):
        return None  # TODO
