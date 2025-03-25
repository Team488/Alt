"""
Reef state tracking system.

This module provides functionality for tracking the state of the reef elements
in the competition field. It maintains probabilistic maps of coral slot
availability and algae presence, and provides methods for querying the best
available slots based on various criteria.
"""

import math
from typing import Dict, Optional, List
import json

import numpy as np
from tools.Constants import ATLocations, ReefBranches, TEAM
from Core import getLogger
from tools.Units import LengthType, RotationType
from coreinterface.ReefPacket import ReefPacket
from assets.schemas import reefStatePacket_capnp

from JXTABLES import XTableValues_pb2 as XTableValue
Sentinel = getLogger("Reef_State")

class ReefState:
    """
    Track and manage the state of the reef elements on the competition field.
    
    This class maintains probability maps for both coral slots and algae presence.
    It provides a Bayesian update system where new observations are integrated
    with the current belief state. The state dissipates over time, representing
    increasing uncertainty when no observations are available for a period.
    
    Attributes:
        idx_flip: Index where red team AprilTags start (after blue team)
        idx_to_apriltag: List mapping internal indices to AprilTag IDs
        apriltag_to_idx: Dictionary mapping AprilTag IDs to internal indices
        reef_map: 2D array of coral slot occupancy probabilities [branch][apriltag]
        algae_map: 1D array of algae presence probabilities by AprilTag
        DISSIPATIONFACTOR: Rate at which certainty dissipates over time
    """
    
    def __init__(self, DISSIPATIONFACTOR=0.999) -> None:
        """
        Initialize a new ReefState tracker.
        
        Args:
            DISSIPATIONFACTOR: Rate of dissipation for certainty over time (0.999 = slow)
        """
        (
            self.idx_flip,
            self.idx_to_apriltag,
            self.apriltag_to_idx,
            self.reef_map,
        ) = self.__createReefMap()
        self.algae_map = self.__createAlgaeMap()
        self.DISSIPATIONFACTOR = DISSIPATIONFACTOR

    def __createReefMap(self) -> tuple[int, list[int], Dict[int, int], np.ndarray]:
        """
        Create and initialize the reef map data structures.
        
        This method initializes:
        1. The mapping indices between AprilTag IDs and internal array indices
        2. The 2D reef map with slots for both teams
        
        Returns:
            Tuple containing:
            - Index where red team slots begin
            - List mapping indices to AprilTag IDs
            - Dictionary mapping AprilTag IDs to indices
            - Initial 2D reef map array
        """
        idx_to_apriltag_blue = ATLocations.getReefBasedIds(TEAM.BLUE)
        idx_to_apriltag_red = ATLocations.getReefBasedIds(TEAM.RED)
        idx_flip = len(idx_to_apriltag_blue)  # index of team flip
        idx_to_apriltag = idx_to_apriltag_blue + idx_to_apriltag_red
        apriltag_to_idx = {}
        for idx, apriltag in enumerate(idx_to_apriltag):
            apriltag_to_idx[apriltag] = idx

        cols = len(idx_to_apriltag)
        rows = len(ReefBranches)
        reef_map = np.full(
            (rows, cols), 0.5, dtype=np.float64
        )  # Initialize to 50% as "unknown"

        return idx_flip, idx_to_apriltag, apriltag_to_idx, reef_map

    def __createAlgaeMap(self):
        """
        Create and initialize the algae presence map.
        
        This method sets up a 1D array that tracks the probability of
        algae presence at each AprilTag location.
        
        Returns:
            Initial algae map array initialized to zeros (no algae)
        """
        idx_to_apriltag = ATLocations.getReefBasedIds()
        numAlgae = len(idx_to_apriltag)
        algae_map = np.zeros((numAlgae), dtype=np.float64)
        return algae_map

    def dissipateOverTime(self, timeFactor: int) -> None:
        """
        Apply time-based dissipation to the belief state.
        
        As time passes without new observations, the system becomes less certain
        about slot availability. This method decreases the confidence in open slots
        by a factor proportional to elapsed time, moving probabilities toward 0.5
        (unknown state).
        
        Args:
            timeFactor: Number of time units that have passed since the last update
        """
        # Reef Map Dissipation
        coral_dissipation_factor = np.power(
            self.DISSIPATIONFACTOR, round(timeFactor / 5)
        )

        # Create a mask for slots that are not locked (not -1) and above 0.5 to dissipate
        # That way we can keep "unknown" states
        mask = (self.reef_map != -1) & (self.reef_map > 0.5)

        # Apply the new dissipation
        new_coral_map = (
            0.5 + (self.reef_map[mask] - 0.5) * coral_dissipation_factor
        )  # discrete dissipation

        # Epsilon Threshold to reset detections approaching 0.5
        epsilon = 1e-1
        new_coral_map[np.abs(new_coral_map - 0.5) < epsilon] = 0.5

        # Update the reef map:
        self.reef_map[mask] = new_coral_map

        # Algae Map Dissipation
        algae_dissipation_factor = np.power(
            self.DISSIPATIONFACTOR, round(timeFactor / 10)
        )
        self.algae_map *= algae_dissipation_factor  # discrete dissipation

    def addObservationCoral(
        self, apriltagid, branchid, opennessconfidence, weighingfactor=0.85
    ) -> None:
        """
        Add a coral slot observation to the reef map.
        
        Updates the belief state for a specific coral slot based on a new
        observation, using a weighted average of the current belief and the
        new observation. Implements a locking mechanism when slots are observed
        to be definitely filled.
        
        Args:
            apriltagid: AprilTag ID where the observation was made
            branchid: Branch ID (vertical position) of the observation
            opennessconfidence: Probability that the slot is open (0-1)
            weighingfactor: Weight to give the new observation vs. prior belief
        """
        if apriltagid not in self.apriltag_to_idx or (
            branchid < 0 or branchid >= self.reef_map.shape[0]
        ):
            Sentinel.warning(
                f"Invalid apriltagid or branchid! {apriltagid=} {branchid=}"
            )
            return

        col_idx = self.apriltag_to_idx.get(apriltagid)
        row_idx = branchid

        # Locking mechanism: If we're very confident a slot is filled (< 0.1 openness),
        # lock it permanently by setting it to -1.0
        if self.reef_map[row_idx, col_idx] < 0.1:
            self.reef_map[row_idx, col_idx] = -1.0
            return

        # Weighted average update
        self.reef_map[row_idx, col_idx] *= 1 - weighingfactor
        self.reef_map[row_idx, col_idx] += opennessconfidence * weighingfactor

    def addObservationAlgae(
        self, apriltagid, opennessconfidence, weighingfactor=0.85
    ) -> None:
        """
        Add an algae presence observation to the algae map.
        
        Updates the belief state for algae presence at a specific AprilTag
        based on a new observation. Implements a locking mechanism when
        algae is definitively observed to be present.
        
        Args:
            apriltagid: AprilTag ID where the observation was made
            opennessconfidence: Probability that no algae is present (0-1)
            weighingfactor: Weight to give the new observation vs. prior belief
        """
        if apriltagid not in self.apriltag_to_idx:
            Sentinel.warning(f"Invalid apriltagid{apriltagid=}")
            return

        algae_idx = self.apriltag_to_idx.get(apriltagid)

        # Locking mechanism for the algae (we only care when it's definitely present)
        if self.algae_map[algae_idx] > 0.95:
            self.algae_map[algae_idx] = 1.0

        # Skip if locked
        if self.algae_map[algae_idx] == 1.0:
            return

        # Weighted average update
        self.algae_map[algae_idx] *= 1 - weighingfactor
        self.algae_map[algae_idx] += opennessconfidence * weighingfactor

    def getOpenSlotsAboveT(
        self,
        team: TEAM = None,
        threshold=0.5,
        algaeThreshold=0.7,
        considerAlgaeBlocking=True,
    ) -> list[tuple[int, int, float]]:
        """
        Get a list of coral slots that are likely to be open.
        
        Finds all slots with an openness probability above the specified threshold,
        optionally filtering by team and considering algae blocking.
        
        Args:
            team: Optional team filter (BLUE, RED, or None for all)
            threshold: Minimum openness probability to consider a slot open
            algaeThreshold: Threshold above which algae is considered present
            considerAlgaeBlocking: Whether to exclude slots blocked by algae
            
        Returns:
            List of tuples with (AprilTag ID, branch ID, openness confidence)
            for each open slot
        """
        offset_col, mapbacking = self.__getMapBacking(team)
        row_idxs, col_idxs = np.where(mapbacking > threshold)

        open_slots = []
        for row, col in zip(row_idxs, col_idxs):
            at_idx = self.idx_to_apriltag[col + offset_col]
            branch_idx = row

            blockedBranchIdxs = ATLocations.getBlockedBranchIdxs(at_idx)
            algaeOccupancy = self.algae_map[self.apriltag_to_idx[at_idx]]

            openness = mapbacking[row, col]

            # If we are checking for algae blocking and the branch is one that could be blocked,
            # and if we meet the algae occupancy threshold, ignore this slot
            if considerAlgaeBlocking and (
                algaeOccupancy > algaeThreshold and branch_idx in blockedBranchIdxs
            ):
                Sentinel.debug(f"Blocked algae at {at_idx=} {row=} {blockedBranchIdxs}")
                continue

            open_slots.append((int(at_idx), int(branch_idx), float(openness)))

        return open_slots

    def getHighestSlot(self, team: TEAM = None) -> Optional[tuple[int, int, float]]:
        """
        Get the slot with the highest openness probability.
        
        Finds the coral slot with the maximum openness probability,
        optionally filtering by team.
        
        Args:
            team: Optional team filter (BLUE, RED, or None for all)
            
        Returns:
            Tuple with (AprilTag ID, branch ID, openness confidence) for the
            slot with highest openness probability, or None if no slots available
        """
        offset_col, mapbacking = self.__getMapBacking(team)
        if not (mapbacking > 0).any():
            return None

        max = np.argmax(mapbacking)
        row, col = np.unravel_index(max, mapbacking.shape)
        branch_idx = row
        at_idx = self.idx_to_apriltag[col + offset_col]
        openness = mapbacking[row, col]

        return at_idx, branch_idx, openness

    # Helper
    def getReefMapState_as_dictionary(
        self, team: TEAM = None
    ) -> dict[(int, int):float]:
        """
        Get the entire reef map state as a dictionary.
        
        Creates a dictionary representation of the reef map state,
        with keys as (AprilTag ID, branch ID) tuples and values as
        openness probabilities.
        
        Args:
            team: Optional team filter (BLUE, RED, or None for all)
            
        Returns:
            Dictionary mapping (AprilTag ID, branch ID) to openness probability
        """
        offset_col, mapbacking = self.__getMapBacking(team)
        reefMap_state = {}
        rows, cols = mapbacking.shape
        for col in range(cols):
            for row in range(rows):
                at_id = self.idx_to_apriltag[col + offset_col]
                openness = mapbacking[row, col]
                reefMap_state[(int(at_id), int(row))] = float(openness)

        return reefMap_state

    def getReefMapState_as_ReefPacket(
        self, team: TEAM = None, timestamp=0
    ) -> reefStatePacket_capnp.ReefPacket:
        # Create the Coral Map Output
        offset_col, mapbacking = self.__getMapBacking(team)
        coralTrackerOutput = {}
        rows, cols = mapbacking.shape
        for col in range(cols):
            for row in range(rows):
                at_id = self.idx_to_apriltag[col + offset_col]
                openness = mapbacking[row, col]
                if at_id not in coralTrackerOutput:
                    coralTrackerOutput[at_id] = {}
                coralTrackerOutput[at_id][row] = openness
        # Create the Algae Map Output
        algaeTrackerOutput = {}
        for apriltag in self.idx_to_apriltag:
            algae_idx = self.apriltag_to_idx.get(apriltag)
            algaeTrackerOutput[apriltag] = self.algae_map[algae_idx]

        message = "Reef State Update"
        return ReefPacket.createPacket(
            coralTrackerOutput, algaeTrackerOutput, message, timestamp
        )
    
    def getReefMapState_as_protobuf(
            self, team: TEAM = None, timestamp=0
    ) -> XTableValue.ReefState:
        reef_state_proto = XTableValue.ReefState()
        reef_state_entries : List[XTableValue.ReefEntry] = []

        # Create the Coral Map Output
        offset_col, mapbacking = self.__getMapBacking(team)
        rows, cols = mapbacking.shape
        for col in range(cols):
            at_id = self.idx_to_apriltag[col + offset_col]
            reef_entry = XTableValue.ReefEntry()
            branch_coral_state_lst : List[XTableValue.BranchCoralState] = []
            for row in range(rows):
                openness = mapbacking[row, col]
                branch_coral_state = XTableValue.BranchCoralState()
                branch_coral_state.index = row + 1
                branch_coral_state.openness = openness
                branch_coral_state_lst.append(branch_coral_state)
            reef_entry.aprilTagID = at_id
            reef_entry.algaeOpenness = self.apriltag_to_idx.get(at_id)
            reef_entry.branchIndexStates.extend(branch_coral_state_lst)

            reef_state_entries.append(reef_entry)

        reef_state_proto.entries.extend(reef_state_entries)
        return reef_state_proto

    def getReefMapState_as_Json(
        self, team: TEAM = None, timestamp=0
    ) -> reefStatePacket_capnp.ReefPacket:
        # Create the Coral Map Output
        offset_col, mapbacking = self.__getMapBacking(team)
        coralTrackerOutput = {}
        rows, cols = mapbacking.shape
        for col in range(cols):
            for row in range(rows):
                at_id = self.idx_to_apriltag[col + offset_col]
                openness = mapbacking[row, col]
                if at_id not in coralTrackerOutput:
                    coralTrackerOutput[at_id] = {}
                coralTrackerOutput[at_id][row] = openness
        # Create the Algae Map Output
        algaeTrackerOutput = {}
        for apriltag in self.idx_to_apriltag:
            algae_idx = self.apriltag_to_idx.get(apriltag)
            algaeTrackerOutput[apriltag] = self.algae_map[algae_idx]

        jsonstr = json.dumps((coralTrackerOutput, algaeTrackerOutput))
        return jsonstr

    def __getMapBacking(self, team: TEAM):
        """
        Get the appropriate segment of the reef map based on team.
        
        This helper method returns the relevant portion of the reef map
        based on the specified team, along with the column offset needed
        for index calculations.
        
        Args:
            team: Optional team filter (BLUE, RED, or None for all)
            
        Returns:
            Tuple with (column offset, map segment)
        """
        mapbacking = self.reef_map
        offset_col = 0
        if team is not None:
            if team == TEAM.BLUE:
                mapbacking = mapbacking[:, : self.idx_flip]
            elif team == TEAM.RED:
                mapbacking = mapbacking[:, self.idx_flip :]
                offset_col = self.idx_flip
        return offset_col, mapbacking

    def __getDist(self, robotPos2CMRAd: tuple[float, float, float], atId: int):
        """
        Calculate the distance from robot to an AprilTag.
        
        Computes the Euclidean distance between the robot's current position
        and the specified AprilTag's position.
        
        Args:
            robotPos2CMRAd: Robot position as (x, y, yaw) in centimeters and radians
            atId: AprilTag ID to find distance to
            
        Returns:
            Distance in centimeters between robot and AprilTag
        """
        atPoseXYCM = ATLocations.get_pose_by_id(atId, length=LengthType.CM)[0][:2]
        robotXYCm = robotPos2CMRAd[:2]
        return np.linalg.norm((np.subtract(atPoseXYCM, robotXYCm)))

    def getClosestOpen(
        self,
        robotPos2CMRAd: tuple[float, float, float],
        team: TEAM = None,
        threshold=0.5,
        algaeThreshold=0.7,
        considerAlgaeBlocking=True,
    ):
        """
        Find the closest open coral slot to the robot's current position.
        
        This method:
        1. Gets all open slots meeting the threshold criteria
        2. Calculates the distance from the robot to each AprilTag
        3. Returns the closest AprilTag and its branch
        
        Args:
            robotPos2CMRAd: Robot position as (x, y, yaw) in centimeters and radians
            team: Optional team filter (BLUE, RED, or None for all)
            threshold: Minimum openness probability to consider a slot open
            algaeThreshold: Threshold above which algae is considered present
            considerAlgaeBlocking: Whether to exclude slots blocked by algae
            
        Returns:
            Tuple of (AprilTag ID, branch ID) for the closest open slot,
            or (None, None) if no open slots are found
        """
        open_slots = self.getOpenSlotsAboveT(
            team, threshold, algaeThreshold, considerAlgaeBlocking
        )
        closestAT = None
        closestBranch = None
        closestDist = 1e6
        for atid, branchid, _ in open_slots:
            if closestAT != atid:
                # skip same tag if already checked that one as the closest
                d = self.__getDist(robotPos2CMRAd, atid)
                if d < closestDist:
                    closestAT = atid
                    closestBranch = branchid
                    closestDist = d

        return closestAT, closestBranch
