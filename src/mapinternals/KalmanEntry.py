from typing import Any

class KalmanEntry:
    def __init__(self, X: Any, P: Any) -> None:
        self.X = X
        self.P = P
        self.framesNotSeen = 0

    def incrementNotSeen(self) -> None:
        self.framesNotSeen += 1
