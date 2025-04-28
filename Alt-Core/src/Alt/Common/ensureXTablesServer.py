import os
import requests
import platform
import subprocess
from pathlib import Path
from .files import __get_user_data_dir, download_file

__LATESTXTABLEPATH = "https://github.com/Kobeeeef/XTABLES/releases/download/v5.0.0/XTABLES.jar"

def __check_mdns_exists(hostname):
    import socket
    try:
        ip = socket.gethostbyname(hostname)
        print(f"{hostname} resolved to {ip}")
        return True
    except socket.gaierror:
        print(f"{hostname} not found")
        return False


def ensureXTablesServer():
    if __check_mdns_exists("XTables.local"):
        print("xtables server already running")
        return

    print("Trying to start xtables server.....")
    target_dir = __get_user_data_dir()
    xtables_path = target_dir / "XTABLES.jar"

    if not xtables_path.is_file():
        try:
            download_file(__LATESTXTABLEPATH, xtables_path)
        except requests.exceptions.RequestException as e:
            print(f"Failed network request: {e}")
            return

    try:
        # Use Popen to run the process asynchronously
        process = subprocess.Popen(["java", "-jar", str(xtables_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Started xtables server in the background with PID {process.pid}")

        # Optionally, you can read the process output asynchronously if you need
        # stdout, stderr = process.communicate()  # You can skip this if you don't need to capture output
        # if process.returncode != 0:
        #     print(f"Java ran but xtables failed to start properly! Error: {stderr.decode()}")
        # else:
        #     print("xtables server started successfully.")

    except FileNotFoundError as e:
        print(f"Java not found or xtables jar missing!\n{e}")
    except subprocess.CalledProcessError as e:
        print(f"Java ran but xtables failed to start properly!\n{e}")
