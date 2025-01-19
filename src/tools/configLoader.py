import json
import codecs

CONFIG_PATH = "/xbot/config"


def loadSavedCalibration():
    try:
        savedCalib = json.load(
            codecs.open(f"{CONFIG_PATH}/camera_calib.json", "r", encoding="utf-8")
        )
        return savedCalib
    except Exception as e:
        print("Error occured when loading calibration, defaulting to saved values", e)
        return {
            "CameraMatrix": [
                [541.6373297834168, 0.0, 350.2246103229324],
                [0.0, 542.5632693416148, 224.8432462256541],
                [0.0, 0.0, 1.0],
            ],
            "DistortionCoeff": [
                [
                    0.03079145286029344,
                    -0.0037492997547329213,
                    -0.0009340163324388664,
                    0.0012027838051384778,
                    -0.07882030659375006,
                ]
            ],
        }


def loadOpiConfig():
    try:
        savedCalib = json.load(
            codecs.open(f"{CONFIG_PATH}/orangepi_config.json", "r", encoding="utf-8")
        )
        return savedCalib
    except Exception as e:
        print("Error occured when loading config, defaulting to saved values", e)
        return {
            "positionTable": "/AdvantageKit/RealOutputs/PoseSubsystem/RobotPose",
            "useXTablesForPos": False,
        }
