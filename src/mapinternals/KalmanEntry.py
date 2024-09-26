class KalmanEntry:
    def __init__(self, X, P):
        self.X = X
        self.P = P
        self.framesNotSeen = 0

    def incrementNotSeen(self):
        self.framesNotSeen += 1
