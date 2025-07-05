"""files.py

Utility functions for handling application-specific file and directory operations,
such as determining user data and temporary directories, and downloading files.

This module provides:
- Cross-platform user data and temporary directory resolution for the application.
- A simple file downloader using HTTP(S).
"""

import os
import platform
import requests
import tempfile
from pathlib import Path

APPNAME = "Alt"


def __get_user_data_dir() -> Path:
    """
    Determines and returns the path to the application's user data directory,
    creating it if it does not exist.

    The location is platform-dependent:
    - Windows: Uses LOCALAPPDATA or APPDATA.
    - macOS: ~/Library/Application Support/Alt
    - Linux/Other: ~/.local/share/Alt

    Returns:
        Path: The path to the application's user data directory.
    """
    system = platform.system()

    if system == "Windows":
        local_app_data = os.getenv("LOCALAPPDATA")
        app_data = os.getenv("APPDATA")
        assert local_app_data is not None
        assert app_data is not None
        base_dir = Path(local_app_data or app_data)
    elif system == "Darwin":  # MacOS
        base_dir = Path.home() / "Library" / "Application Support"
    else:  # Linux and others
        base_dir = Path.home() / ".local" / "share"

    app_dir = base_dir / APPNAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir


user_data_dir = __get_user_data_dir()


def __get_user_tmp_dir() -> Path:
    """
    Determines and returns the path to the application's temporary directory,
    creating it if it does not exist.

    The location is platform-dependent:
    - Windows: Uses TEMP environment variable or system temp directory.
    - macOS/Linux/Other: /tmp/Alt

    Returns:
        Path: The path to the application's temporary directory.
    """
    system = platform.system()

    if system == "Windows":
        base_tmp = Path(os.getenv("TEMP") or tempfile.gettempdir())
    elif system == "Darwin":  # macOS
        base_tmp = Path("/tmp")
    else:  # Linux and others
        base_tmp = Path("/tmp")

    app_tmp_dir = base_tmp / APPNAME
    app_tmp_dir.mkdir(parents=True, exist_ok=True)
    return app_tmp_dir


user_tmp_dir = __get_user_tmp_dir()


def download_file(url, target_path: Path) -> None:
    """
    Downloads a file from the specified URL and saves it to the given target path.

    Args:
        url (str): The URL of the file to download.
        target_path (Path): The local file path where the downloaded file will be saved.

    Raises:
        requests.HTTPError: If the HTTP request returned an unsuccessful status code.
    """
    response = requests.get(url)
    response.raise_for_status()
    target_path.write_bytes(response.content)
    print(f"Downloaded to {target_path}")
