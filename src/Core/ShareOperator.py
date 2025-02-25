from logging import Logger
from threading import Lock


class ShareOperator:
    """ "Temporary Memory" to be shared between any agents and orders"""

    def __init__(self, logger: Logger) -> None:
        self.__sharedMap = {}
        self.__sharedLock = Lock()
        self.Sentinel = logger

    def put(self, key, value) -> None:
        with self.__sharedLock:
            self.__sharedMap[key] = value

    def get(self, key, default=None):
        with self.__sharedLock:
            return self.__sharedMap.get(key, default)

    def has(self, key) -> bool:
        with self.__sharedLock:
            return key in self.__sharedMap
