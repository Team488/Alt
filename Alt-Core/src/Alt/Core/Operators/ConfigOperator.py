"""ConfigOperator.py

This module provides the ConfigOperator class and ConfigType enum for managing
configuration files in various formats (JSON, NumPy) for the application.
It supports loading, saving, and retrieving configuration data from multiple
paths, including override and default locations.

Classes:
    ConfigType: Enum for supported configuration file types and their handlers.
    ConfigOperator: Handles loading, saving, and accessing configuration files.

Functions:
    (All public and private methods are documented at the class and function level.)
"""

import os
import json
import codecs
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import numpy as np
from enum import Enum

from .LogOperator import getChildLogger
from ..Utils.files import user_data_dir

Sentinel = getChildLogger("Config_Operator")

class ConfigType(Enum):
    """
    Enum representing supported configuration file types and their load/save handlers.
    """
    NUMPY = "numpy"
    JSON = "json"

    @staticmethod
    def load_numpy(path: str) -> Any:
        """
        Load a NumPy array from a file.

        Args:
            path (str): Path to the .npy file.

        Returns:
            Any: The loaded NumPy array.
        """
        return np.load(path)

    @staticmethod
    def load_json(path: str) -> Any:
        """
        Load JSON data from a file.

        Args:
            path (str): Path to the .json file.

        Returns:
            Any: The loaded JSON data.
        """
        return json.load(codecs.open(path, "r", encoding="utf-8"))

    @staticmethod
    def save_numpy(path: str, content: Any) -> None:
        """
        Save a NumPy array to a file.

        Args:
            path (str): Path to save the .npy file.
            content (Any): The NumPy array to save.
        """
        np.save(path, content)

    @staticmethod
    def save_json(path: str, content: Any) -> None:
        """
        Save data as JSON to a file.

        Args:
            path (str): Path to save the .json file.
            content (Any): The data to save as JSON.
        """
        with open(path, "w", encoding="utf-8") as f:
            json.dump(content, f)

    def load(self, path: str) -> Any:
        """
        Load data from a file using the appropriate handler based on the config type.

        Args:
            path (str): Path to the file.

        Returns:
            Any: The loaded data.

        Raises:
            ValueError: If the config type is unsupported.
        """
        if self == ConfigType.NUMPY:
            return ConfigType.load_numpy(path)
        elif self == ConfigType.JSON:
            return ConfigType.load_json(path)
        else:
            raise ValueError(f"Unsupported config type: {self}")

    def save(self, path: str, content: Any) -> None:
        """
        Save data to a file using the appropriate handler based on the config type.

        Args:
            path (str): Path to the file.
            content (Any): The data to save.

        Raises:
            ValueError: If the config type is unsupported.
        """
        if self == ConfigType.NUMPY:
            return ConfigType.save_numpy(path, content)
        elif self == ConfigType.JSON:
            return ConfigType.save_json(path, content)
        else:
            raise ValueError(f"Unsupported config type: {self}")

class ConfigOperator:
    """
    Handles loading, saving, and accessing configuration files in various formats.

    Supports multiple search and save paths, including override and default locations.
    Provides methods for static and instance-based loading and saving of config files.
    """

    OVERRIDE_CONFIG_PATH: str = (
        "/xbot/Alt"  # if you want to override any json configs, put here
    )
    OVERRIDE_PROPERTY_CONFIG_PATH: str = "/xbot/Alt/PROPERTIES"
    DEFAULT_CONFIG_PATH: str = str(user_data_dir)
    DEFAULT_PROPERTY_CONFIG_PATH: str = str(user_data_dir / "PROPERTIES")
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
        """
        Initialize the ConfigOperator and load configuration files from all read paths.
        """
        self.configMap: Dict[str, Any] = {}
        for path in self.READPATHS:
            self.__loadFromPath(path)
        # loading override second means that it will overwrite anything set by default.
        # NOTE: if you only specify a subset of the .json file in the override, you will loose the default values.

    def __loadFromPath(self, path: str) -> None:
        """
        Load all known config files from a directory into the config map.

        Args:
            path (str): Directory path to load config files from.
        """
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
        """
        Save content to a JSON file in each configured save path.

        Args:
            filename (str): Name of the file to save.
            content (Any): Data to save as JSON.
        """
        for path in self.SAVEPATHS:
            filePath = os.path.join(path, filename)
            self.__saveToFileJSON(filePath, content)

    def savePropertyToFileJSON(self, filename: str, content: Any) -> None:
        """
        Save property content to a JSON file in each configured property save path.

        Args:
            filename (str): Name of the property file to save.
            content (Any): Data to save as JSON.
        """
        for path in self.SAVEPATHS:
            filePath = os.path.join(f"{path}/PROPERTIES", filename)
            self.__saveToFileJSON(filePath, content)

    def __saveToFileJSON(self, filepath: str, content: Any) -> bool:
        """
        Save content to a JSON file at the specified path.

        Args:
            filepath (str): Full path to save the file.
            content (Any): Any JSON-serializable content to save.

        Returns:
            bool: True if save was successful, False otherwise.
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
        Get content for a filename from the config map.

        Args:
            filename (str): Name of the config file to retrieve.
            default (Any, optional): Default value to return if file not found.

        Returns:
            Any: Content of the file or default if not found.
        """
        return self.configMap.get(filename, default)

    def getAllFileNames(self) -> List[str]:
        """
        Get a list of all loaded config file names.

        Returns:
            List[str]: List of config file names.
        """
        return list(self.configMap.keys())
    
    @staticmethod
    def staticLoad(
        fileName: str
    ) -> Optional[Tuple[Any, float]]:
        """
        Load a file from one of the configured save paths and return its content and modification time.

        Args:
            fileName (str): The name of the file to load.

        Returns:
            Optional[Tuple[Any, float]]: A tuple of (file_content, modification_time) or None if file not found or unloadable.
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

        return None
    
    @staticmethod
    def staticWrite(
        filename: str, content: Any, config_type: ConfigType
    ) -> bool:
        """
        Try to save content to all configured save paths using the given config type.

        Args:
            filename (str): Name of the file to write (should include correct extension).
            content (Any): The data to be saved.
            config_type (ConfigType): The format in which to save the data (e.g. JSON, NUMPY).

        Returns:
            bool: True if save to at least one path succeeded, False otherwise.
        """
        success = False
        for path in ConfigOperator.SAVEPATHS:
            try:
                file_path = os.path.join(path, filename)
                dir_path = os.path.dirname(file_path)
                os.makedirs(dir_path, exist_ok=True)
                config_type.save(file_path, content)
                success = True
            except Exception as e:
                Sentinel.debug(e)
                Sentinel.info(f"Failed to write to {file_path}")
        return success


