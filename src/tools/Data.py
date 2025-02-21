from typing import Any


class CircularBuffer:
    def __init__(self, bufferSize: int):
        self.head = -bufferSize
        self.tail = 0
        self.backing = [] * bufferSize

    def put(self, value: Any):
        ptr = self.tail
        self.backing[ptr] = value
