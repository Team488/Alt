import os
import json
import codecs
from logging import Logger
import numpy as np
from enum import Enum


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
    OVERRIDE_CONFIG_PATH = "/xbot/config" # if you want to override any json configs, put here
    DEFAULT_CONFIG_PATH = "assets" # default configs
    knownFileEndings = ((".npy", ConfigType.NUMPY), (".json", ConfigType.JSON))
    def __init__(self, logger : Logger):
        self.Sentinel = logger 
        self.__loadFromPath(self.DEFAULT_CONFIG_PATH)
        self.__loadFromPath(self.OVERRIDE_CONFIG_PATH)
        self.configMap = {}
        # loading override second means that it will overwrite anything set by default. 
        # NOTE: if you only specify a subset of the .json file in the override, you will loose the default values.  

    def __loadFromPath(self, path):
        try:
            for filename in os.listdir(path):
                file_path = os.path.join(path, filename)
                for (ending,filetype) in self.knownFileEndings:
                    if file_path.endswith(ending):
                        self.Sentinel.info(f"Loaded config file from {file_path}")
                        content = filetype.load(file_path)
                        self.Sentinel.debug(f"File content: {content}")
                        self.configMap[filename] = content
        except Exception as agentSmith:
            # override config path dosent exist
            self.Sentinel.debug(f"{path} does not exist. likely not critical")

    def getContent(self, filename):
        return self.configMap.get(filename, None)

    



