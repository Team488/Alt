class KalmanEntry:
    def __init__(self, X, P) -> None:
        self.X = X
        self.P = P
        self.framesNotSeen = 0

    def incrementNotSeen(self) -> None:
        self.framesNotSeen += 1
