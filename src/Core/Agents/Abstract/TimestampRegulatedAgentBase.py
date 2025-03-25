"""
Timestamp Regulated Agent Base Module - For timestamp synchronization between data sources

This module provides the TimestampRegulatedAgentBase class, which combines the capabilities
of CameraUsingAgentBase and PositionLocalizingAgentBase while adding timestamp
synchronization. This allows agents to match camera frames with position data based
on their timestamps, ensuring temporal coherence in processing.

The timestamp regulation is implemented using a binning approach, where data items
from different sources are grouped into time bins of a specified size. This helps
handle the challenges of working with asynchronous data sources that may have
slightly different sampling rates or timing characteristics.

This class serves as a foundation for agents that need to correlate visual data
with positional data, such as object trackers, navigation systems, and SLAM
implementations.
"""

import cv2
from typing import Dict, Any, Tuple, Optional
from Core.Agents.Abstract.CameraUsingAgentBase import CameraUsingAgentBase
from Core.Agents.Abstract.PositionLocalizingAgentBase import PositionLocalizingAgentBase


class TimestampRegulatedAgentBase(CameraUsingAgentBase, PositionLocalizingAgentBase):
    """
    Base class for agents that need to synchronize timestamps between data sources.
    
    This class extends both CameraUsingAgentBase and PositionLocalizingAgentBase,
    combining their capabilities and adding timestamp synchronization. It uses a
    binning approach to match camera frames with position data based on their
    timestamps, ensuring temporal coherence in processing.
    
    The inheritance hierarchy is:
    Agent -> (CameraUsingAgentBase, PositionLocalizingAgentBase) -> TimestampRegulatedAgentBase
    
    Attributes:
        BINSIZE: Size of timestamp bins in milliseconds
        binnedMap: Dictionary mapping timestamp bins to data items
        
    Notes:
        This class should always be extended, not used directly.
    """

    BINSIZE: int = 5  # whatever the timestamp units are in, likely MS but todo figure out

    def __init__(self, **kwargs: Any) -> None:
        """
        Initialize a new TimestampRegulatedAgentBase instance.
        
        Args:
            **kwargs: Keyword arguments passed to parent class constructors
        """
        super().__init__(**kwargs)
        self.binnedMap: Dict[int, Any] = {}

    def runPeriodic(self) -> None:
        """
        Execute the agent's periodic processing logic.
        
        This method is called regularly by the agent framework and
        inherits functionality from both CameraUsingAgentBase and
        PositionLocalizingAgentBase. It's intended to be extended
        by subclasses to implement timestamp synchronization logic.
        
        Notes:
            Subclasses should implement timestamp binning logic to
            match camera frames with position data.
        """
        super().runPeriodic()
        # Timestamp binning logic to be implemented by subclasses
