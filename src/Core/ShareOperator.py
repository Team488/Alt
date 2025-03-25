"""
Share Operator Module - Thread-safe shared memory system for inter-component communication

This module provides a centralized, thread-safe mechanism for different components
(such as agents and orders) to exchange temporary data throughout the system. It serves
as a simple in-memory key-value store protected by thread synchronization.

The ShareOperator is typically used for:
- Passing data between agents that need to cooperate
- Sharing temporary state that doesn't need to be persisted
- Creating dynamic, short-lived relationships between components

All operations are thread-safe, using a lock to prevent race conditions when
multiple threads access the shared data simultaneously.

Example:
    # Store a value
    shareOperator.put("camera_frame", frame)
    
    # Check if a key exists
    if shareOperator.has("object_detections"):
        # Retrieve a value
        detections = shareOperator.get("object_detections")
"""

from logging import Logger
from threading import Lock
from typing import Any, Dict, Optional, TypeVar, Generic

T = TypeVar('T')

class ShareOperator:
    """
    Thread-safe shared memory system for data exchange between agents and orders.
    
    Provides a centralized mechanism for agents and orders to share temporary data
    throughout the system. All operations are thread-safe using a Lock.
    
    Attributes:
        Sentinel: Logger instance for reporting errors and diagnostic information
    """

    def __init__(self, logger: Logger) -> None:
        """
        Initialize a new ShareOperator instance.
        
        Args:
            logger: Logger instance to use for reporting issues
        """
        self.__sharedMap: Dict[str, Any] = {}
        self.__sharedLock = Lock()
        self.Sentinel = logger

    def put(self, key: str, value: Any) -> None:
        """
        Store a value in the shared memory with the given key.
        
        Args:
            key: String identifier to associate with the value
            value: Any value to store in shared memory
        """
        with self.__sharedLock:
            self.__sharedMap[key] = value

    def get(self, key: str, default: Optional[T] = None) -> Optional[Any]:
        """
        Retrieve a value from shared memory by its key.
        
        Args:
            key: String identifier associated with the desired value
            default: Value to return if the key doesn't exist (default: None)
            
        Returns:
            The value associated with the key, or the default value if the key doesn't exist
        """
        with self.__sharedLock:
            return self.__sharedMap.get(key, default)

    def has(self, key: str) -> bool:
        """
        Check if a key exists in the shared memory.
        
        Args:
            key: String identifier to check
            
        Returns:
            True if the key exists in shared memory, False otherwise
        """
        with self.__sharedLock:
            return key in self.__sharedMap
