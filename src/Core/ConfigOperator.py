import os
import json
import codecs
from pathlib import Path
from logging import Logger
import numpy as np
from enum import Enum


def staticLoad(fileName: str):
    for path in ConfigOperator.SAVEPATHS:
        try:
            filePath = os.path.join(path, fileName)
            for (ending, filetype) in ConfigOperator.knownFileEndings:
                if filePath.endswith(ending):
                    content = filetype.load(filePath)
                    return content

            print(
                f"Invalid file ending. Options are: {[ending[0] for ending in ConfigOperator.knownFileEndings]}"
            )
        except Exception as agentSmith:
            # override config path dosent exist
            print(agentSmith)
            print(f"{path} does not exist!")

    return None


class ConfigType(Enum):
    NUMPY = "numpy"
    JSON = "json"

    @staticmethod
    def load_numpy(path):
        return np.load(path)

    @staticmethod
    def load_json(path):
        return json.load(codecs.open(path, "r", encoding="utf-8"))

    def load(self, path):
        if self == ConfigType.NUMPY:
            return ConfigType.load_numpy(path)
        elif self == ConfigType.JSON:
            return ConfigType.load_json(path)


class ConfigOperator:
    OVERRIDE_CONFIG_PATH = (
        "/xbot/config"  # if you want to override any json configs, put here
    )
    OVERRIDE_PROPERTY_CONFIG_PATH = "/xbot/config/PROPERTIES"
    DEFAULT_CONFIG_PATH = "assets"  # default configs
    DEFAULT_PROPERTY_CONFIG_PATH = "assets/PROPERTIES"
    SAVEPATHS = [OVERRIDE_CONFIG_PATH, DEFAULT_CONFIG_PATH]
    READPATHS = [
        OVERRIDE_CONFIG_PATH,
        DEFAULT_CONFIG_PATH,
        OVERRIDE_PROPERTY_CONFIG_PATH,
        DEFAULT_PROPERTY_CONFIG_PATH,
    ]
    knownFileEndings = ((".npy", ConfigType.NUMPY), (".json", ConfigType.JSON))

    def __init__(self, logger: Logger) -> None:
        self.Sentinel = logger
        self.configMap = {}
        for path in self.READPATHS:
            self.__loadFromPath(path)
        # loading override second means that it will overwrite anything set by default.
        # NOTE: if you only specify a subset of the .json file in the override, you will loose the default values.

    def __loadFromPath(self, path) -> None:
        try:
            for filename in os.listdir(path):
                filePath = os.path.join(path, filename)
                for (ending, filetype) in self.knownFileEndings:
                    if filename.endswith(ending):
                        self.Sentinel.info(f"Loaded config file from {filePath}")
                        content = filetype.load(filePath)
                        self.Sentinel.debug(f"File content: {content}")
                        self.configMap[filename] = content
        except Exception as agentSmith:
            # override config path dosent exist
            self.Sentinel.debug(agentSmith)
            self.Sentinel.info(f"{path} does not exist. likely not critical")

    def saveToFileJSON(self, filename, content) -> None:
        for path in self.SAVEPATHS:
            filePath = os.path.join(path, filename)
            self.__saveToFileJSON(filePath, content)

    def savePropertyToFileJSON(self, filename, content) -> None:
        for path in self.SAVEPATHS:
            filePath = os.path.join(f"{path}/PROPERTIES", filename)
            self.__saveToFileJSON(filePath, content)

    def __saveToFileJSON(self, filepath: str, content) -> bool:  # is success
        try:
            path = Path(filepath)
            directoryPath = path.parent.as_posix()

            if not os.path.exists(directoryPath):
                os.mkdir(directoryPath)  # only one level
                self.Sentinel.debug(f"Created PROPERTIES path in {directoryPath}")
            with open(filepath, "w") as file:
                json.dump(content, file)
            return True
        except Exception as agentSmith:
            self.Sentinel.debug(agentSmith)
            self.Sentinel.info(f"{filepath} does not exist. likely not critical")
            return False

    def getContent(self, filename, default=None):
        return self.configMap.get(filename, default)

    def getAllFileNames(self):
        return list(self.configMap.keys())
