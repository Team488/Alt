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
    STREAMPATH = "stream.mjpg"

    def __init__(self, app : Flask, manager: multiprocessing.managers.SyncManager):
        self.app = app
        self.streams : Dict[str, StreamProxy] = {}  # Dictionary to store streams
        self.manager = manager  # Multiprocessing Manager
        self.running = True

    def register_stream(self, name) -> "StreamProxy":
        """Creates a new stream, registers a route, and returns a DictProxy for updating frames."""
        if name in self.streams:
            Sentinel.info(f"Stream {name} already exists.")
            return self.streams[name]["dict"]

        # Create a new DictProxy from the manager
        streamPath = f"http://{DEVICEIP}:5000/{name}/{self.STREAMPATH}"
        streamProxy = StreamProxy(self.manager.dict(), streamPath)

        
        self.streams[name] = streamProxy

        # Define the stream generation function dynamically
        def generate_frames(streamProxy : StreamProxy):
            """Generator function to yield MJPEG frames."""
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

    def _create_view_func(self, generate_frames_func, name):
        """Helper to create a view function for a dynamic stream with stream handling."""

        @functools.wraps(generate_frames_func)
        def view_func():
            return Response(
                stream_with_context(generate_frames_func()),  # Stream with context
                mimetype="multipart/x-mixed-replace; boundary=frame",
            )

        view_func.__name__ = f"stream_{name}_view"
        return view_func


    def shutdown(self):
        """Stops all streams and shuts down the server."""
        Sentinel.info("Shutting down MJPEG server...")
        for name in list(self.streams.keys()):
            self.close_stream(name)

        self.running = False

    def close_stream(self, name):
        """Closes a specific stream and releases the resources."""
        if name in self.streams:
            del self.streams[name]
            Sentinel.info(f"Closed stream: {name}")


class StreamProxy(Proxy):
    """ Wrapper around multiprocessing.managers.DictProxy
        Allows you to put interact with a stream you created, from another process
    """
    def __init__(self, streamDict: managers.DictProxy, streamPath : str):
        self.__streamDict = streamDict
        self.__streamDict["stream_path"] = streamPath

    def put(self, frame : np.ndarray) -> None:
        self.__streamDict["frame"] = frame
        self.__streamDict["frame_count"] = self.__streamDict.get("frame_count", 0) + 1

    def get(self) -> Optional[np.ndarray]:
        return self.__streamDict.get("frame")
    
    def getFrameCount(self) -> Optional[int]:
        return self.__streamDict.get("frame_count")
    
    def getStreamPath(self) -> str:
        return self.__streamDict.get("stream_path")

    
    """ For pickling"""

    def __getstate__(self):
        return self.__streamDict

    def __setstate__(self, state):
        self.__streamDict = state