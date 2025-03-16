from logging import Logger
from threading import Lock
from typing import Any, Dict, Optional, TypeVar, Generic

T = TypeVar('T')

class ShareOperator:
    """ "Temporary Memory" to be shared between any agents and orders"""

    def __init__(self, logger: Logger) -> None:
        self.__sharedMap: Dict[str, Any] = {}
        self.__sharedLock = Lock()
        self.Sentinel = logger

    def put(self, key: str, value: Any) -> None:
        with self.__sharedLock:
            self.__sharedMap[key] = value

    def get(self, key: str, default: Optional[T] = None) -> Optional[Any]:
        with self.__sharedLock:
            return self.__sharedMap.get(key, default)

    def has(self, key: str) -> bool:
        with self.__sharedLock:
            return key in self.__sharedMap
