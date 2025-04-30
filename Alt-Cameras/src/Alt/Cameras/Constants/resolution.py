from enum import Enum

class OAKDLITEResolution(Enum):
    OAK4K = (3840, 2160, 30)
    OAK1080P = (1920, 1080, 60)

    @property
    def fps(self):
        return self.value[2]

    @property
    def w(self):
        return self.value[0]

    @property
    def h(self):
        return self.value[1]


class D435IResolution(Enum):
    RS720P = (1280, 720, 30)
    RS480P = (640, 480, 60)

    @property
    def fps(self):
        return self.value[2]

    @property
    def w(self):
        return self.value[0]

    @property
    def h(self):
        return self.value[1]