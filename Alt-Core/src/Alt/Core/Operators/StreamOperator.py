import threading
import functools
import multiprocessing
import time
import cv2
import hashlib
from flask import Flask, Response, stream_with_context
from multiprocessing import managers
import numpy as np
from werkzeug.serving import make_server
from .LogOperator import getChildLogger





Sentinel = getChildLogger("Stream_Operator")


class StreamOperator:

    def __init__(self, app : Flask, manager: multiprocessing.managers.SyncManager):
        self.app = app
        self.streams = {}  # Dictionary to store streams
        self.manager = manager  # Multiprocessing Manager
        self.running = True

    def _frame_hash(self, frame):
        return hashlib.md5(frame).digest()

    def register_stream(self, name) -> managers.DictProxy:
        """Creates a new stream, registers a route, and returns a DictProxy for updating frames."""
        if name in self.streams:
            Sentinel.info(f"Stream {name} already exists.")
            return self.streams[name]["dict"]

        # Create a new DictProxy from the manager
        frameShare = self.manager.dict()
        self.streams[name] = {"dict": frameShare}

        # Define the stream generation function dynamically
        def generate_frames(shareddict=frameShare):
            """Generator function to yield MJPEG frames."""
            lastHashF = None
            while self.running:
                frame = shareddict.get("frame", None)
                hashf = self._frame_hash(frame)
                if frame is None or hashf == lastHashF:
                    time.sleep(0.01)
                    continue

                lastHashF = hashf
                ret, jpeg = cv2.imencode(".jpg", frame)
                if not ret:
                    continue
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n\r\n"
                )

        self.app.add_url_rule(
            f"/{name}/stream.mjpg",
            view_func=self._create_view_func(generate_frames, name),
        )

        Sentinel.info(f"Registered new stream: {name} at '{name}/stream.mjpg'")
        return frameShare

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
