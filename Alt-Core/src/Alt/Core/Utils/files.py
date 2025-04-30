import os
import platform
import requests
import tempfile
from pathlib import Path

APPNAME = "Alt"

def __get_user_data_dir() -> Path:
    system = platform.system()

    if system == "Windows":
        base_dir = Path(os.getenv('LOCALAPPDATA') or os.getenv('APPDATA'))
    elif system == "Darwin":  # MacOS
        base_dir = Path.home() / "Library" / "Application Support"
    else:  # Linux and others
        base_dir = Path.home() / ".local" / "share"

    app_dir = base_dir / APPNAME
    app_dir.mkdir(parents=True, exist_ok=True)
    return app_dir

user_data_dir = __get_user_data_dir() 



def __get_user_tmp_dir() -> Path:
    system = platform.system()

    if system == "Windows":
        base_tmp = Path(os.getenv('TEMP') or tempfile.gettempdir())
    elif system == "Darwin":  # macOS
        base_tmp = Path("/tmp")
    else:  # Linux and others
        base_tmp = Path("/tmp")

    app_tmp_dir = base_tmp / APPNAME
    app_tmp_dir.mkdir(parents=True, exist_ok=True)
    return app_tmp_dir

user_tmp_dir = __get_user_tmp_dir() 


def download_file(url, target_path: Path) -> None:
    response = requests.get(url)
    response.raise_for_status()
    target_path.write_bytes(response.content)
    print(f"Downloaded to {target_path}")