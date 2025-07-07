"""ShareOperator.py

Provides the ShareOperator class for sharing data between agents using a multiprocessing dictionary.

Classes:
    ShareOperator: Uses a multiprocessing dict to share memory across agents.
"""

from __future__ import annotations

from typing import Any, Optional
from .LogOperator import getChildLogger

Sentinel = getChildLogger("Share_Operator")


class ShareOperator:
    """
    Uses a multiprocessing dict to "share memory" across any agents locally.

    Args:
        dict: The multiprocessing dictionary to use for shared state.
    """

    def __init__(self, dict) -> None:
        """
        Initializes the ShareOperator with a multiprocessing dictionary.

        Args:
            dict: The multiprocessing dictionary to use for shared state.
        """
        self.__sharedMap = dict

    def put(self, key: str, value: Any) -> None:
        """
        Store a value in the shared map.

        Args:
            key (str): The key under which to store the value.
            value (Any): The value to store.
        """
        self.__sharedMap[key] = value

    def get(self, key: str, default: Optional[Any] = None) -> Optional[Any]:
        """
        Retrieve a value from the shared map.

        Args:
            key (str): The key to look up.
            default (Any, optional): The default value if the key is not found.

        Returns:
            Any: The value associated with the key, or the default if not found.
        """
        return self.__sharedMap.get(key, default)

    def has(self, key: str) -> bool:
        """
        Check if a key exists in the shared map.

        Args:
            key (str): The key to check.

        Returns:
            bool: True if the key exists, False otherwise.
        """
        return key in self.__sharedMap

    """ For pickling"""

    def __getstate__(self):
        """
        Get the state for pickling.

        Returns:
            dict: The shared map.
        """
        return self.__sharedMap

    def __setstate__(self, state):
        """
        Set the state from pickling.

        Args:
            state (dict): The shared map to restore.
        """
        self.__sharedMap = state
