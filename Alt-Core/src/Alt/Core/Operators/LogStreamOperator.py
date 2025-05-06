"""LogStreamOperator.py

Provides the LogStreamOperator class for managing server-sent event (SSE) log streams
using Flask endpoints and multiprocessing queues.

Classes:
    LogStreamOperator: Registers and manages log streams for SSE endpoints.
"""

import queue
from flask import Flask, Response, stream_with_context
import functools
import multiprocessing
from queue import Empty
from .LogOperator import getChildLogger

Sentinel = getChildLogger("Log_Stream_Operator")


class LogStreamOperator:
    """
    Registers and manages log streams for SSE endpoints using Flask and multiprocessing queues.

    Attributes:
        LOGPATH (str): The path segment for log streaming endpoints.
        app (Flask): The Flask application instance.
        manager (multiprocessing.managers.SyncManager): The multiprocessing manager.
        log_streams (dict): Dictionary to store log queues.
        running (bool): Indicates if the log stream operator is running.
    """
    LOGPATH = "logs"
    def __init__(self, app: Flask, manager: multiprocessing.managers.SyncManager):
        """
        Initializes the LogStreamOperator.

        Args:
            app (Flask): The Flask application instance.
            manager (multiprocessing.managers.SyncManager): The multiprocessing manager.
        """
        self.app = app
        self.manager = manager
        self.log_streams : dict[str, dict[str, queue.Queue]] = {}  # Dictionary to store log queues
        self.running = True

    def register_log_stream(self, name : str) -> queue.Queue:
        """
        Registers a new SSE log stream and returns a Queue for pushing logs to it.

        Args:
            name (str): The name of the log stream.

        Returns:
            queue.Queue: The queue for pushing logs to the stream.
        """
        if name in self.log_streams:
            Sentinel.info(f"Log stream {name} already exists.")
            return self.log_streams[name]["queue"]

        log_queue = self.manager.Queue()
        self.log_streams[name] = {"queue": log_queue}

        def generate_logs(queue=log_queue):
            """
            Yields logs from a multiprocessing queue as Server-Sent Events.
            """
            while self.running:
                try:
                    log_line = queue.get(timeout=0.1)
                    yield f"data: {log_line}\n\n"
                except Empty:
                    continue

        self.app.add_url_rule(
            f"/{name}/{self.LOGPATH}",
            view_func=self._create_log_view_func(generate_logs, name),
        )

        Sentinel.info(f"Registered new log stream: {name} at '/{name}/logs'")
        return log_queue

    def _create_log_view_func(self, generator_func, name):
        """
        Creates a view function to stream logs using SSE.

        Args:
            generator_func (callable): The generator function for log streaming.
            name (str): The name of the log stream.

        Returns:
            function: The Flask view function for the log stream.
        """
        @functools.wraps(generator_func)
        def view_func():
            response = Response(
                stream_with_context(generator_func()),
                mimetype="text/event-stream",
            )
            response.headers["Cache-Control"] = "no-cache"
            response.headers["Access-Control-Allow-Origin"] = "*"
            response.headers["Access-Control-Allow-Headers"] = "Content-Type"
            response.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
            return response

        view_func.__name__ = f"log_stream_{name}_view"
        return view_func

    def shutdown(self):
        """
        Stops all log streams and clears the log stream dictionary.
        """
        Sentinel.info("Shutting down log stream operator...")
        self.running = False
        self.log_streams.clear()
