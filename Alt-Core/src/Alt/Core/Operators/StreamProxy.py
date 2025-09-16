from __future__ import annotations

import numpy as np
from multiprocessing import managers
from typing import Optional
from .LogOperator import getChildLogger
from ..Constants.AgentConstants import Proxy

Sentinel = getChildLogger("Stream_Operator")

class StreamProxy(Proxy):
    """Wrapper for accessing and manipulating a stream from another process.

    This class extends the DictProxy used to transfer data
    between processes, specifically for MJPEG video streaming.

    Attributes:
        __streamDict (managers.DictProxy): The underlying dictionary proxy
        holding stream data.
    """

    def __init__(self, streamDict: managers.DictProxy, streamPath: str):
        """Initializes a StreamProxy instance.

        Args:
            streamDict (managers.DictProxy): Proxy for accessing shared data.
            streamPath (str): URL path of the video stream.
        """
        self.__streamDict = streamDict
        self.__streamDict["stream_path"] = streamPath
        self.__streamDict["frame_count"] = 0

    def put(self, frame: np.ndarray) -> None:
        """Stores a new video frame in the proxy.

        Args:
            frame (np.ndarray): The video frame to store.
        """
        self.__streamDict["frame"] = frame
        self.__streamDict["frame_count"] = self.__streamDict.get("frame_count", 0) + 1

    def get(self) -> Optional[np.ndarray]:
        """Retrieves the current video frame from the proxy.

        Returns:
            Optional[np.ndarray]: The latest frame, or None if no frame is available.
        """
        return self.__streamDict.get("frame")

    def getFrameCount(self) -> int:
        """Gets the current count of frames stored in the proxy.

        Returns:
            int: The total number of frames sent.
        """
        return self.__streamDict["frame_count"]

    def getStreamPath(self) -> str:
        """Gets the URL path of the video stream.

        Returns:
            str: The path where the stream can be accessed.
        """
        return self.__streamDict["stream_path"]

    def __getstate__(self):
        """Returns the state of the StreamProxy for pickling.

        This method enables the StreamProxy to be correctly serialized.

        Returns:
            managers.DictProxy: The underlying stream dictionary proxy.
        """
        return self.__streamDict

    def __setstate__(self, state):
        """Restores the state of the StreamProxy from a pickled state.

        Args:
            state (dict): The state to restore from.
        """
        self.__streamDict = state
