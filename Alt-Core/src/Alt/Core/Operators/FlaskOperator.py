"""FlaskOperator.py

Provides a FlaskOperator class to manage a Flask web server in a background thread,
with easy start and shutdown capabilities for integration into multiprocessing or threaded applications.

Classes:
    FlaskOperator: Manages the lifecycle of a Flask server in a separate thread.
"""

from __future__ import annotations

import threading
from flask import Flask
from werkzeug.serving import make_server
from .LogOperator import getChildLogger


Sentinel = getChildLogger("Stream_Operator")


class FlaskOperator:
    """
    Manages a Flask web server running in a background thread.

    Attributes:
        PORT (int): The port the server listens on.
        HOST (str): The host address the server binds to.
        app (Flask): The Flask application instance.
        server (BaseWSGIServer): The WSGI server instance.
        server_thread (threading.Thread): The thread running the server.
        running (bool): Indicates if the server is running.
    """

    PORT = 5000
    HOST = "0.0.0.0"

    def __init__(self):
        """
        Initializes the FlaskOperator, setting up the Flask app and server thread.
        """
        self.app = Flask(__name__)
        self.server = None
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.running = False

    def run_server(self):
        """
        Runs the Flask server using a WSGI server with shutdown capability.
        This method is intended to be run in a background thread.
        """
        self.running = True
        self.server = make_server(self.HOST, self.PORT, self.app, threaded=True)
        self.server.serve_forever()

    def start(self):
        """
        Starts the Flask server in a background thread.
        """
        self.server_thread.start()
        Sentinel.info(f"Flask Server running at {self.HOST}:{self.PORT}")

    def getApp(self):
        """
        Returns the Flask application instance.

        Returns:
            Flask: The Flask app.
        """
        return self.app

    def shutdown(self):
        """
        Stops and shuts down the server, waiting for the server thread to finish.
        """
        if self.server:
            self.server.shutdown()  # Properly shuts down the server

        self.server_thread.join()
        Sentinel.info("Flask Server stopped.")
