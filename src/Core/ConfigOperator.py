"""
Configuration management system for loading and saving settings across the Alt system.

This module provides the ConfigOperator class that handles loading configuration from
multiple possible locations with override capabilities, and saving configuration data
to persistent storage. It supports multiple file formats like JSON and NumPy arrays.

The module defines a flexible configuration hierarchy where files in override paths
take precedence over default paths, allowing for runtime configuration changes without
modifying source files.
"""

import os
import json
import codecs
from pathlib import Path
from logging import Logger
from typing import Dict, List, Any, Optional, Tuple, Union, Type, cast
import numpy as np
from enum import Enum
from Core import getLogger 

Sentinel = getLogger("Config_Operator")

def staticLoad(fileName: str) -> Optional[Tuple[Any, float]]:
    """
    Load a file from one of the configured save paths and return its content and modification time.
    
    Args:
        fileName: The name of the file to load
        
    Returns:
        A tuple of (file_content, modification_time) or None if file not found or unloadable
    """
    for path in ConfigOperator.SAVEPATHS:
        try:
            filePath = os.path.join(path, fileName)
            for (ending, filetype) in ConfigOperator.knownFileEndings:
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


class ConfigType(Enum):
    """
    Enumeration of supported configuration file types with loading functions.
    
    This enum defines the supported file types for configuration storage and provides
    methods to load each type from disk.
    
    Attributes:
        NUMPY: NumPy array file type
        JSON: JSON file type
    """
    NUMPY = "numpy"
    JSON = "json"

    @staticmethod
    def load_numpy(path: str) -> Any:
        """
        Load a NumPy file from the specified path.
        
        Args:
            path: Path to the NumPy file
            
        Returns:
            The loaded NumPy array
        """
        return np.load(path)

    @staticmethod
    def load_json(path: str) -> Any:
        """
        Load a JSON file from the specified path.
        
        Args:
            path: Path to the JSON file
            
        Returns:
            The loaded JSON data as Python objects
        """
        return json.load(codecs.open(path, "r", encoding="utf-8"))

    def load(self, path: str) -> Any:
        """
        Load a file of this config type from the specified path.
        
        Args:
            path: Path to the configuration file
            
        Returns:
            The loaded configuration data
            
        Raises:
            ValueError: If the config type is not supported
        """
        if self == ConfigType.NUMPY:
            return ConfigType.load_numpy(path)
        elif self == ConfigType.JSON:
            return ConfigType.load_json(path)
        else:
            raise ValueError(f"Unsupported config type: {self}")


class ConfigOperator:
    """
    Manages loading and saving configuration files from multiple locations.
    
    This class handles the loading of configuration files from both default and
    override paths, allowing for runtime configuration changes without modifying
    source files. It supports multiple file formats including JSON and NumPy arrays.
    
    Configurations are loaded in a specific order, with override paths taking precedence
    over default paths. This ensures that runtime or environment-specific configurations
    can override the default values.
    
    Attributes:
        OVERRIDE_CONFIG_PATH: Path for override configuration files
        OVERRIDE_PROPERTY_CONFIG_PATH: Path for override property configuration files
        DEFAULT_CONFIG_PATH: Path for default configuration files
        DEFAULT_PROPERTY_CONFIG_PATH: Path for default property configuration files
        SAVEPATHS: List of paths to save configuration files to
        READPATHS: List of paths to read configuration files from
        knownFileEndings: Tuple of supported file extensions and their ConfigType
        configMap: Dictionary mapping filenames to their loaded content
    """
    
    OVERRIDE_CONFIG_PATH: str = (
        "/xbot/config"  # if you want to override any json configs, put here
    )
    OVERRIDE_PROPERTY_CONFIG_PATH: str = "/xbot/config/PROPERTIES"
    DEFAULT_CONFIG_PATH: str = "assets"  # default configs
    DEFAULT_PROPERTY_CONFIG_PATH: str = "assets/PROPERTIES"
    SAVEPATHS: List[str] = [OVERRIDE_CONFIG_PATH, DEFAULT_CONFIG_PATH]
    READPATHS: List[str] = [
        OVERRIDE_CONFIG_PATH,
        DEFAULT_CONFIG_PATH,
        OVERRIDE_PROPERTY_CONFIG_PATH,
        DEFAULT_PROPERTY_CONFIG_PATH,
    ]
    knownFileEndings: Tuple[Tuple[str, ConfigType], ...] = (
        (".npy", ConfigType.NUMPY), 
        (".json", ConfigType.JSON)
    )

    def __init__(self) -> None:
        """
        Initialize the ConfigOperator and load configuration files from all defined paths.
        
        Loads configuration files from all paths defined in READPATHS. Files in override
        paths take precedence over those in default paths, allowing for runtime configuration
        changes without modifying default files.
        """
        self.configMap: Dict[str, Any] = {}
        for path in self.READPATHS:
            self.__loadFromPath(path)
        # loading override second means that it will overwrite anything set by default.
        # NOTE: if you only specify a subset of the .json file in the override, you will loose the default values.

    def __loadFromPath(self, path: str) -> None:
        """
        Load all configuration files from a specified path into the config map.
        
        Args:
            path: Directory path to load configuration files from
        """
        try:
            for filename in os.listdir(path):
                filePath = os.path.join(path, filename)
                for (ending, filetype) in self.knownFileEndings:
                    if filename.endswith(ending):
                        Sentinel.info(f"Loaded config file from {filePath}")
                        content = filetype.load(filePath)
                        Sentinel.debug(f"File content: {content}")
                        self.configMap[filename] = content
        except Exception as agentSmith:
            # override config path dosent exist
            Sentinel.debug(agentSmith)
            Sentinel.info(f"{path} does not exist. likely not critical")

    def saveToFileJSON(self, filename: str, content: Any) -> None:
        """
        Save content to a JSON file in each configured save path.
        
        Args:
            filename: Name of the file to save
            content: JSON-serializable content to save
        """
        for path in self.SAVEPATHS:
            filePath = os.path.join(path, filename)
            self.__saveToFileJSON(filePath, content)

    def savePropertyToFileJSON(self, filename: str, content: Any) -> None:
        """
        Save property content to a JSON file in each configured property save path.
        
        This method specifically saves to the PROPERTIES subdirectory of each save path.
        
        Args:
            filename: Name of the property file to save
            content: JSON-serializable property content to save
        """
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
        """
        Get a list of all loaded config file names.
        
        Returns:
            List of strings containing all loaded configuration file names
        """
        return list(self.configMap.keys())
