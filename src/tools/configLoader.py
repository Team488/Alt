import json
import codecs

import numpy as np
CONFIG_PATH = "/xbot/config"
DEFAULT_CONFIG_PATH = "assets"


# config paths in order of priority    
def loadJsonConfig(config_file,config_paths=[CONFIG_PATH,DEFAULT_CONFIG_PATH]):
    for config_path in config_paths:
        try:
            savedCalib = json.load(
                codecs.open(f"{config_path}/{config_file}", "r", encoding="utf-8")
            )
            print(f"Loaded config from {config_path}/{config_file}")
            return savedCalib
        except Exception as e:
            pass
    return None

# config paths in order of priority    
def loadNumpyConfig(numpy_file,config_paths=[CONFIG_PATH,DEFAULT_CONFIG_PATH]):
    for config_path in config_paths:
        try:
            npObject = np.load(f"{config_path}/{numpy_file}")
            print(f"Loaded config from {config_path}/{numpy_file}")
            return npObject
        except Exception as e:
            pass
    return None


def loadSavedCalibration():
    savedCalib = loadJsonConfig("camera_calib.json")
    if savedCalib is not None:
        return savedCalib
    print("Fatal! No backup config. Should never hit this as long as one stays in the assets dir")

    
def loadOpiConfig():
    opiConfig = loadJsonConfig("orangepi_config.json")
    if opiConfig is not None:
        return opiConfig
    print("Fatal! No backup config. Should never hit this as long as one stays in the assets dir")
    
    
def loadRedRobotHistogram():
    redHist = loadNumpyConfig("redRobotHist.npy")
    if redHist is not None:
        return redHist
    print("Fatal! No backup hist. Should never hit this as long as one stays in the assets dir")

def loadBlueRobotHistogram():
    blueHist = loadNumpyConfig("blueRobotHist.npy")
    if blueHist is not None:
        return blueHist
    print("Fatal! No backup hist. Should never hit this as long as one stays in the assets dir")