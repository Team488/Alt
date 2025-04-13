import threading
from flask import Flask
from werkzeug.serving import make_server
from .LogOperator import getChildLogger





Sentinel = getChildLogger("Stream_Operator")


class FlaskOperator:
    PORT = 5000
    HOST ="0.0.0.0"

    def __init__(self):
        self.app = Flask(__name__)
        self.server = None
        self.server_thread = threading.Thread(target=self.run_server, daemon=True)
        self.running = False


    def run_server(self):
        """Runs the Flask server using a WSGI server with shutdown capability."""
        self.running = True
        self.server = make_server(self.HOST, self.PORT, self.app, threaded=True)
        self.server.serve_forever()

    def start(self):
        """Starts the Flask server in a background thread."""
        self.server_thread.start()
        Sentinel.info(f"Flask Server running at {self.HOST}:{self.PORT}")

    def getApp(self):
        return self.app

    def shutdown(self):
        """Stops and shuts down the server."""
        if self.server:
            self.server.shutdown()  # Properly shuts down the server

        self.server_thread.join()
        Sentinel.info("Flask Server stopped.")

