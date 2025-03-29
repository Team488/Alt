import functools
import multiprocessing
import cv2
from flask import Flask, Response, request
from multiprocessing import Manager, managers
import threading
from Core import getChildLogger
from werkzeug.serving import make_server

Sentinel = getChildLogger("Stream_Operator")


class StreamOperator:
    PORT = 5000

    def __init__(self, manager: multiprocessing.managers.SyncManager, host="0.0.0.0"):
        self.app = Flask(__name__)
        self.host = host
        self.streams = {}  # Dictionary to store
        self.manager = manager  # Multiprocessing Manager
        self.server = None
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
                frame = shareddict.get("frame", None)
                if frame is None:
                    continue
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
        """Helper to create a view function for a dynamic stream with functools.wraps."""
        @functools.wraps(generate_frames_func)
        def view_func():
            return Response(
                generate_frames_func(),
                mimetype="multipart/x-mixed-replace; boundary=frame",
            )
        view_func.__name__ = f"stream_{name}_view"
        return view_func

    def run_server(self):
        """Runs the Flask server in a separate thread."""
        self.server = make_server(self.host, self.PORT, self.app)
        self.server.serve_forever()

    def start(self):
        """Starts the Flask server in a background thread."""
        self.server_thread.start()
        Sentinel.info(f"MJPEG Server running at {self.host}:{self.PORT}")

    def shutdown(self):
        """Stops all streams and shuts down the server."""
        Sentinel.info("Shutting down MJPEG server...")
        for name in list(self.streams.keys()):
            self.close_stream(name)
        if self.server:
            print("AAAA")
            self.server.shutdown()
        self.server_thread.join()
        Sentinel.info("MJPEG Server stopped.")

    def close_stream(self, name):
        """Closes a specific stream and releases the resources."""
        if name in self.streams:
            self.streams[name]["dict"]["frame"] = None
            del self.streams[name]
            Sentinel.info(f"Closed stream: {name}")