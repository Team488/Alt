import os
import numpy as np
import paramiko


TMPSYNCPATH = "assets/TMPSync"
REGULARSYNCPATH = "assets"
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


def saveNpy(fileName: str, npObj, filePath=REGULARSYNCPATH):
    if not fileName.endswith(".npy"):
        fileName = f"{fileName}.npy"

    fullPath = os.path.join(filePath, fileName)
    slashIdx1 = fullPath.rfind("\\\\")
    slashIdx2 = fullPath.rfind("//")

    bestSlash = slashIdx1 if slashIdx1 > slashIdx2 else slashIdx2
    if bestSlash != -1:
        pathOnly = fullPath[:bestSlash]
        os.makedirs(pathOnly, exist_ok=True)

    np.save(fullPath, npObj)
    print(f"Saved at {fullPath}")


def saveToTempNpy(fileName: str, npObj):
    saveNpy(fileName, npObj, fileName=TMPSYNCPATH)


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
