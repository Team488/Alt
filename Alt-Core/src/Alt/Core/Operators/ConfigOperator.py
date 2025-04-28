import os
import json
import codecs
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from enum import Enum
from .LogOperator import getChildLogger
from ...Common.files import user_data_dir

Sentinel = getChildLogger("Config_Operator")


def staticLoad(
    fileName: str, isRelativeToSource: bool = False
) -> Optional[Tuple[Any, float]]:
    """
    Load a file from one of the configured save paths and return its content and modification time.

    Args:
        fileName: The name of the file to load

    Returns:
        A tuple of (file_content, modification_time) or None if file not found or unloadable
    """
    # first look in override pathW
    for path in ConfigOperator.SAVEPATHS:
        try:
            filePath = os.path.join(path, fileName)
            for ending, filetype in ConfigOperator.knownFileEndings:
                if filePath.endswith(ending):
                    content = filetype.load(filePath)
                    mtime = os.path.getmtime(filePath)
                    return content, mtime

            Sentinel.fatal(
                f"Invalid file ending. Options are: {[ending[0] for ending in ConfigOperator.knownFileEndings]}"
            )
        except Exception as agentSmith:
            # probably override config path dosent exist
            Sentinel.debug(agentSmith)
            Sentinel.debug(f"{path} does not exist!")

    # try relative to source after trying override paths
    if isRelativeToSource:
        try:
            basePath = os.path.join(os.path.abspath(os.path.dirname(__file__)), "..")
            filePath = os.path.join(basePath, fileName)
            for ending, filetype in ConfigOperator.knownFileEndings:
                if filePath.endswith(ending):
                    content = filetype.load(filePath)
                    mtime = os.path.getmtime(filePath)
                    return content, mtime
        except Exception as agentSmith:
            Sentinel.debug(agentSmith)
            Sentinel.debug(f"{path} does not exist!")

    return None


class ConfigType(Enum):
    NUMPY = "numpy"
    JSON = "json"

    @staticmethod
    def load_numpy(path: str) -> Any:
        return np.load(path)

    @staticmethod
    def load_json(path: str) -> Any:
        return json.load(codecs.open(path, "r", encoding="utf-8"))

    def load(self, path: str) -> Any:
        if self == ConfigType.NUMPY:
            return ConfigType.load_numpy(path)
        elif self == ConfigType.JSON:
            return ConfigType.load_json(path)
        else:
            raise ValueError(f"Unsupported config type: {self}")


class ConfigOperator:
    OVERRIDE_CONFIG_PATH: str = (
        "/xbot/config"  # if you want to override any json configs, put here
    )
    OVERRIDE_PROPERTY_CONFIG_PATH: str = "/xbot/config/PROPERTIES"
    DEFAULT_CONFIG_PATH: str = user_data_dir / "Assets"
    DEFAULT_PROPERTY_CONFIG_PATH: str = user_data_dir / "PROPERTIES"
    SAVEPATHS: List[str] = [OVERRIDE_CONFIG_PATH, DEFAULT_CONFIG_PATH]
    READPATHS: List[str] = [
        OVERRIDE_CONFIG_PATH,
        DEFAULT_CONFIG_PATH,
        OVERRIDE_PROPERTY_CONFIG_PATH,
        DEFAULT_PROPERTY_CONFIG_PATH,
    ]
    knownFileEndings: Tuple[Tuple[str, ConfigType], ...] = (
        (".npy", ConfigType.NUMPY),
        (".json", ConfigType.JSON),
    )

    def __init__(self) -> None:
        self.configMap: Dict[str, Any] = {}
        for path in self.READPATHS:
            self.__loadFromPath(path)
        # loading override second means that it will overwrite anything set by default.
        # NOTE: if you only specify a subset of the .json file in the override, you will loose the default values.

    def __loadFromPath(self, path: str) -> None:
        try:
            for filename in os.listdir(path):
                filePath = os.path.join(path, filename)
                for ending, filetype in self.knownFileEndings:
                    if filename.endswith(ending):
                        # Sentinel.info(f"Loaded config file from {filePath}")
                        content = filetype.load(filePath)
                        # Sentinel.debug(f"File content: {content}")
                        self.configMap[filename] = content
        except Exception as agentSmith:
            # override config path dosent exist
            Sentinel.debug(agentSmith)
            Sentinel.info(f"{path} does not exist. likely not critical")

    def saveToFileJSON(self, filename: str, content: Any) -> None:
        """Save content to a JSON file in each configured save path"""
        for path in self.SAVEPATHS:
            filePath = os.path.join(path, filename)
            self.__saveToFileJSON(filePath, content)

    def savePropertyToFileJSON(self, filename: str, content: Any) -> None:
        """Save property content to a JSON file in each configured property save path"""
        for path in self.SAVEPATHS:
            filePath = os.path.join(f"{path}/PROPERTIES", filename)
            self.__saveToFileJSON(filePath, content)

    def __saveToFileJSON(self, filepath: str, content: Any) -> bool:  # is success
        """
        Save content to a JSON file at the specified path

        Args:
            filepath: Full path to save the file
            content: Any JSON-serializable content to save

        Returns:
            True if save was successful, False otherwise
        """
        try:
            path = Path(filepath)
            directoryPath = path.parent.as_posix()

            if not os.path.exists(directoryPath):
                os.mkdir(directoryPath)  # only one level
                Sentinel.debug(f"Created PROPERTIES path in {directoryPath}")
            with open(filepath, "w") as file:
                json.dump(content, file)
            return True
        except Exception as agentSmith:
            Sentinel.debug(agentSmith)
            Sentinel.info(f"{filepath} does not exist. likely not critical")
            return False

    def getContent(self, filename: str, default: Any = None) -> Any:
        """
        Get content for a filename from the config map

        Args:
            filename: Name of the config file to retrieve
            default: Default value to return if file not found

        Returns:
            Content of the file or default if not found
        """
        return self.configMap.get(filename, default)

    def getAllFileNames(self) -> List[str]:
        """Get a list of all loaded config file names"""
        return list(self.configMap.keys())
