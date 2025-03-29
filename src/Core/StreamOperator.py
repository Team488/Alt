import functools
import multiprocessing
import os
import signal
import cv2
from flask import Flask, Response
from multiprocessing import Manager, managers
import threading
from Core import getChildLogger

Sentinel = getChildLogger("Stream_Operator")


class StreamOperator:
    PORT = 5000

    def __init__(self, manager: multiprocessing.managers.SyncManager, host="0.0.0.0"):
        self.app = Flask(__name__)
        self.host = host
        self.streams = {}  # Dictionary to store
        self.manager = manager  # Multiprocessing Manager
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)

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
            while True:
                # Get frame from the DictProxy
                frame = frameShare.get("frame", None)  # This will block until a frame is available
                if frame is None:
                    continue
                ret, jpeg = cv2.imencode(".jpg", frame)
                if not ret:
                    continue
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + jpeg.tobytes() + b"\r\n\r\n"
                )

        # Register the route with a unique view function using functools.wraps
        self.app.add_url_rule(
            f"/{name}/stream.mjpg",
            view_func=self._create_view_func(generate_frames, name),
        )

        Sentinel.info(f"Registered new stream: {name} at '{name}/stream.mjpg'")
        return frameShare  # Return the DictProxy so external processes/threads can update it

    def _create_view_func(self, generate_frames_func, name):
        """Helper to create a view function for a dynamic stream with functools.wraps."""
        # Define the view function
        @functools.wraps(generate_frames_func)
        def view_func():
            return Response(
                generate_frames_func(),
                mimetype="multipart/x-mixed-replace; boundary=frame",
            )

        # Set a unique name for the view function based on the stream name
        view_func.__name__ = f"stream_{name}_view"
        return view_func

    def run_server(self):
        """Runs the Flask server in a separate thread."""
        self.app.run(host=self.host, port=self.PORT, threaded=True)

    def start(self):
        """Starts the Flask server in a background thread."""
        self.server_thread.start()
        Sentinel.info(f"MJPEG Server running at {self.host}:{self.PORT}")

    def shutdown(self):
        """Stops all streams and shuts down the server."""
        Sentinel.info("Shutting down MJPEG server...")

        # Close all active streams
        for name in list(
            self.streams.keys()
        ):  # Convert keys to list to avoid modification issues
            self.close_stream(name)

        # Shutdown Flask server (sending SIGINT or SIGTERM)
        # os.kill(os.getpid(), signal.SIGTERM)

        # Ensure server thread stops
        self.server_thread.join()
        Sentinel.info("MJPEG Server stopped.")

    def close_stream(self, name):
        """Closes a specific stream and releases the resources."""
        if name in self.streams:
            dict = self.streams[name]["dict"]
            dict["frame"] = None  # Send a None frame to stop the stream
            del self.streams[name]
            Sentinel.info(f"Closed stream: {name}")
