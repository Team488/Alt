import requests
import subprocess
import socket
from ..Utils.files import __get_user_data_dir, download_file

__LATESTXTABLEPATH = "https://github.com/Kobeeeef/XTABLES/releases/download/v5.0.0/XTABLES.jar"

# Function to check if MDNS hostname is resolved
def __check_mdns_exists(hostname):
    try:
        ip = socket.gethostbyname(hostname)
        print(f"{hostname} resolved to {ip}")
        return True
    except socket.gaierror:
        print(f"{hostname} not found")
        return False

# Function to check if port 4880 is open
def __check_port_open(host="localhost", port=4880):
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(1)  # Set a short timeout for checking the port
    try:
        sock.connect((host, port))
        sock.close()
        print(f"Port {port} is open on {host}. Server is already running.")
        return True
    except (socket.timeout, socket.error):
        return False

# Ensure XTables server is running
def ensureXTablesServer():
    # First, try checking via MDNS
    if __check_mdns_exists("XTables.local"):
        print("XTables server already running (MDNS check).")
        return

    # If MDNS fails, check if port 4880 is open
    if __check_port_open(port=4880):
        print("XTables server already running (Port 4880 check).")
        return

    # If neither MDNS nor port 4880 is open, attempt to start the server
    print("Trying to start XTables server...")

    # Ensure XTables jar is downloaded if it doesn't exist
    target_dir = __get_user_data_dir()
    xtables_path = target_dir / "XTABLES.jar"

    if not xtables_path.is_file():
        try:
            download_file(__LATESTXTABLEPATH, xtables_path)
        except requests.exceptions.RequestException as e:
            print(f"Failed network request: {e}")
            return

    # Attempt to start the server using Java
    try:
        # Use Popen to run the process asynchronously
        process = subprocess.Popen(["java", "-jar", str(xtables_path)], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print(f"Started XTables server in the background with PID {process.pid}")

        # Optionally, you can read the process output asynchronously if needed
        # stdout, stderr = process.communicate()
        # if process.returncode != 0:
        #     print(f"Java ran but XTables failed to start properly! Error: {stderr.decode()}")
        # else:
        #     print("XTables server started successfully.")

    except FileNotFoundError as e:
        print(f"Java not found or XTables jar missing! {e}")
    except subprocess.CalledProcessError as e:
        print(f"Java ran but XTables failed to start properly! {e}")

