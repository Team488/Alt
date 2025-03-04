import os
import numpy as np
import paramiko


TMPSYNCPATH = "assets/TMPSync"
TARGETSYNCPATH = "/xbot/config"


def send_file(hostname, username, password, local_file, remote_file):
    try:
        # Establish SSH connection
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(hostname, username=username, password=password)

        # Start SFTP session
        sftp = client.open_sftp()
        sftp.put(local_file, remote_file)
        sftp.close()

        print(f"File sent to {hostname}")
        client.close()
    except Exception as e:
        print(f"Error on {hostname}: {e}")


def saveToTempNpy(fileName: str, npObj):
    if not fileName.endswith(".npy"):
        fileName = f"{fileName}.npy"
    os.makedirs(TMPSYNCPATH, exist_ok=True)
    np.save(os.path.join(TMPSYNCPATH, fileName), npObj)
    print(f"Saved at {os.path.join(TMPSYNCPATH,fileName)}")


def syncPis(fileName, targetName=None):
    if targetName is None:
        targetName = fileName

    targets = [
        {
            "hostname": "photonvisionfrontright.local",
            "username": "pi",
            "password": "raspberry",
        },
        {
            "hostname": "photonvisionfrontleft.local",
            "username": "pi",
            "password": "raspberry",
        },
        {
            "hostname": "photonvisionback.local",
            "username": "pi",
            "password": "raspberry",
        },
    ]

    # Send file to multiple targets
    for target in targets:
        try:
            send_file(
                target["hostname"],
                target["username"],
                target["password"],
                os.path.join(TMPSYNCPATH, targetName),
                os.path.join(TMPSYNCPATH, targetName),
            )
        except Exception as e:
            print(
                f"Failed to sync target: {target} {fileName=} {targetName=} \nError: {e.with_traceback()}"
            )
