"""
This module provides a streaming service using Flask and multiprocessing.
It allows the registration and management of multiple video streams,
handling frame capture and serving them as MJPEG over HTTP. 
The StreamOperator class manages the streams, while the StreamProxy
class serves as a wrapper for accessing and manipulating the stream data between processes.
"""

import functools
import multiprocessing
import time
import cv2
import numpy as np
from multiprocessing import managers
from typing import Dict, Optional
from flask import Flask, Response, stream_with_context
from werkzeug.serving import make_server
from .LogOperator import getChildLogger
from ...Constants.AgentConstants import Proxy
from ...Common.network import DEVICEIP

Sentinel = getChildLogger("Stream_Operator")

class StreamOperator:
    """Handles the management of multiple MJPEG video streams.

    Responsibilities include:
    - Registering new streams with unique names.
    - Serving video frames as MJPEG over HTTP.
    - Managing the lifecycle of the streams, including starting,
      stopping, and closing them.

    Attributes:
        STREAMPATH (str): The path for MJPEG streaming.
        app (Flask): The Flask application instance for routing.
        streams (Dict[str, StreamProxy]): Dictionary mapping stream names to instances of StreamProxy.
        manager (multiprocessing.managers.SyncManager): Manager for multiprocessing.
        running (bool): Flag to indicate if the server is running.
    """
    
    STREAMPATH = "stream.mjpg"
    
    def __init__(self, app: Flask, manager: multiprocessing.managers.SyncManager):
        """Initializes a StreamOperator instance.

        Args:
            app (Flask): Flask application instance.
            manager (multiprocessing.managers.SyncManager): A Manager for multiprocessing.
        """
        self.app = app
        self.streams: Dict[str, StreamProxy] = {}  # Dictionary to store streams
        self.manager = manager  # Multiprocessing Manager
        self.running = True

    def register_stream(self, name: str) -> "StreamProxy":
        """Creates and registers a new stream, returning a StreamProxy for frame updates.

        Args:
            name (str): Unique name for the stream.

        Returns:
            StreamProxy: The proxy handling the stream's frame data.

        Raises:
            ValueError: If the stream name already exists.
        """
        if name in self.streams:
            Sentinel.info(f"Stream {name} already exists.")
            return self.streams[name]["dict"]

        streamPath = f"http://{DEVICEIP}:5000/{name}/{self.STREAMPATH}"
        streamProxy = StreamProxy(self.manager.dict(), streamPath)

        self.streams[name] = streamProxy
        
        def generate_frames(streamProxy: StreamProxy):
            """Generator function to yield MJPEG frames from the stream proxy.

            This function continuously retrieves frames from the stream
            until the operation is explicitly stopped.

            Args:
                streamProxy (StreamProxy): The proxy to fetch frames from.
            """
            lastCountF = None
            while self.running:
                frame = streamProxy.get()
                countF = streamProxy.getFrameCount()
                if frame is None or countF == lastCountF:
                    time.sleep(0.01)
                    continue
                lastCountF = countF
                ret, jpeg = cv2.imencode(".jpg", frame)
                if not ret:
                    continue
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n\r\n"
                )
        
        self.app.add_url_rule(
            f"/{name}/{self.STREAMPATH}",
            view_func=self._create_view_func(lambda : generate_frames(streamProxy), name),
        )
        Sentinel.info(f"Registered new stream: {name} at '{name}/{self.STREAMPATH}'")
        return streamProxy

    def _create_view_func(self, generate_frames_func, name: str):
        """Creates and returns a view function that serves video stream frames.

        Args:
            generate_frames_func (function): A function that generates video frames.
            name (str): The unique name of the stream.

        Returns:
            function: A Flask view function for serving the video stream.
        """
        @functools.wraps(generate_frames_func)
        def view_func():
            return Response(
                stream_with_context(generate_frames_func()),  # Stream with context
                mimetype="multipart/x-mixed-replace; boundary=frame",
            )
        view_func.__name__ = f"stream_{name}_view"
        return view_func

    def shutdown(self):
        """Stops all active streams and shuts down the server.

        This method halts the operation of the StreamOperator and cleans up
        all registered streams.
        """
        Sentinel.info("Shutting down MJPEG server...")
        for name in list(self.streams.keys()):
            self.close_stream(name)
        self.running = False

    def close_stream(self, name: str):
        """Closes a specific stream and releases associated resources.

        Args:
            name (str): The unique name of the stream to close.
        """
        if name in self.streams:
            del self.streams[name]
            Sentinel.info(f"Closed stream: {name}")

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

    def getFrameCount(self) -> Optional[int]:
        """Gets the current count of frames stored in the proxy.

        Returns:
            Optional[int]: The total number of frames sent, or None if not available.
        """
        return self.__streamDict.get("frame_count")

    def getStreamPath(self) -> str:
        """Gets the URL path of the video stream.

        Returns:
            str: The path where the stream can be accessed.
        """
        return self.__streamDict.get("stream_path")

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