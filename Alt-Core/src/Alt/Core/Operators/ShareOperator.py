from typing import Any, Optional
from .LogOperator import getChildLogger

Sentinel = getChildLogger("Share_Operator")


class ShareOperator:
    """Uses a multiprocessing dict to "share memory" across any agents and orders locally"""

    def __init__(self, dict) -> None:
        self.__sharedMap = dict

    def put(self, key: str, value: Any) -> None:
        self.__sharedMap[key] = value

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        return self.__sharedMap.get(key, default)

    def has(self, key: str) -> bool:
        return key in self.__sharedMap

    """ For pickling"""

    def __getstate__(self):
        return self.__sharedMap

    def __setstate__(self, state):
        self.__sharedMap = state
