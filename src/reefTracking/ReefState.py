import math
from typing import Dict, Optional

import numpy as np
from tools.Constants import ATLocations, ReefBranches, TEAM
from Core import getLogger
from tools.Units import LengthType, RotationType
from coreinterface.ReefPacket import ReefPacket
from assets.schemas import reefStatePacket_capnp

Sentinel = getLogger("Reef_State")
class ReefState:
    def __init__(self, DISSIPATIONFACTOR = 0.8):
        self.idx_flip, self.idx_to_apriltag, self.apriltag_to_idx, self.reef_map = self.__createReefMap()
        self.DISSIPATIONFACTOR = DISSIPATIONFACTOR

    def __createReefMap(self) -> tuple[int, list[int], Dict[int,int], np.ndarray]:
        idx_to_apriltag_blue = ATLocations.getReefBasedIds(TEAM.BLUE)
        idx_to_apriltag_red = ATLocations.getReefBasedIds(TEAM.RED)
        idx_flip = len(idx_to_apriltag_blue) # index of team flip
        idx_to_apriltag = idx_to_apriltag_blue + idx_to_apriltag_red
        apriltag_to_idx = {}
        for idx, apriltag in enumerate(idx_to_apriltag):
            apriltag_to_idx[apriltag] = idx

        cols = len(idx_to_apriltag)
        rows = len(ReefBranches)
        reef_map = np.full((rows,cols), 0.5, dtype=np.float64) # Initialize to 50% as "unknown"

        return idx_flip, idx_to_apriltag, apriltag_to_idx, reef_map

    
    def dissipateOverTime(self, timeFactor : int):
        """ This operates under the assumtion that as time passed, the chance of slots being taken increases. So if there are no updates, as t grows, the openness confidence should go to zero"""
        factor = np.power(self.DISSIPATIONFACTOR, round(timeFactor / 100))
        
        # Create a mask for slots that are not locked (not 0) and above 50 to dissipate
        # That way we can keep "unknown" states
        mask = (self.reef_map != -1) & (self.reef_map > 0.5)
        
        # Only update those slots: they will decay toward 0.5
        self.reef_map[mask] = 0.5 + (self.reef_map[mask] - 0.5) * factor

    def addObservation(self, apriltagid, branchid, opennessconfidence, weighingfactor = 0.85):
        #print(f"AddingObservation", apriltagid, branchid, opennessconfidence)
        if apriltagid not in self.apriltag_to_idx or (branchid < 0 or branchid >= self.reef_map.shape[0]):
            Sentinel.warning(f"Invalid apriltagid or branchid! {apriltagid=} {branchid=}")
            return
        
        col_idx = self.apriltag_to_idx.get(apriltagid)
        row_idx = branchid

        # We know 100% that the space is filled.
        # Stop updating to that particular observation. It is "locked".
        # TODO: Add this in if necessary
        #if self.reef_map[row_idx, col_idx] < 0.1:
            #self.reef_map[row_idx, col_idx] = -1.0
            #return
        
        self.reef_map[row_idx, col_idx] *= (1-weighingfactor)
        self.reef_map[row_idx, col_idx] += opennessconfidence * weighingfactor

    def getOpenSlotsAboveT(self, team : TEAM = None, threshold = 0.5) -> list[tuple[int,int,float]]:
        """ Returns open slots in the form of a tuple with (April tag id, branch id, openness confidence)"""
        offset_col, mapbacking = self.__getMapBacking(team)
        row_idxs, col_idxs = np.where(mapbacking > threshold)

        open_slots = []
        for row, col in zip(row_idxs, col_idxs):
            branch_idx = row
            at_idx = self.idx_to_apriltag[col+offset_col]
            openness = mapbacking[row,col]
            open_slots.append((int(at_idx),int(branch_idx), float(openness)))

        return open_slots

    def getHighestSlot(self, team : TEAM = None) -> Optional[tuple[int,int,float]]:
        """ Returns open slots in the form of a tuple with (April tag id, branch id, openness confidence)"""
        offset_col, mapbacking = self.__getMapBacking(team)
        if not (mapbacking>0).any():
            return None
        
        max = np.argmax(mapbacking)
        row, col = np.unravel_index(max,mapbacking.shape)
        branch_idx = row
        at_idx = self.idx_to_apriltag[col+offset_col]
        openness = mapbacking[row,col]

        return at_idx, branch_idx, openness
    
    # Helper
    def getReefMapState_as_dictionary(self, team: TEAM = None) -> dict[(int, int) : float]: 
        """ Returns the entire map state as a dictionary """
        offset_col, mapbacking = self.__getMapBacking(team)
        reefMap_state = {}
        rows, cols = mapbacking.shape
        for col in range(cols):
            for row in range(rows):
                at_id = self.idx_to_apriltag[col + offset_col]
                openness = mapbacking[row, col]
                reefMap_state[(int(at_id), int(row))] = float(openness)
        
        return reefMap_state

    def getReefMapState_as_ReefPacket(self, team: TEAM = None, timestamp=0) -> reefStatePacket_capnp.ReefPacket:
        offset_col, mapbacking = self.__getMapBacking(team)
        reefTrackerOutput = {}
        rows, cols = mapbacking.shape
        for col in range(cols):
            for row in range(rows):
                at_id = self.idx_to_apriltag[col + offset_col]
                openness = mapbacking[row, col]
                if at_id not in reefTrackerOutput:
                    reefTrackerOutput[at_id] = {}
                reefTrackerOutput[at_id][row] = openness

        message = "Reef State Update"
        return ReefPacket.createPacket(reefTrackerOutput, message, timestamp)

    def __getMapBacking(self, team : TEAM):
        mapbacking = self.reef_map
        offset_col = 0
        if team is not None:
            if team == TEAM.BLUE:
                mapbacking = mapbacking[:, :self.idx_flip]
            elif team == TEAM.RED:
                mapbacking = mapbacking[:, self.idx_flip:]
                offset_col = self.idx_flip
        return offset_col, mapbacking
    
    def __getDist(self, robotPos2CMRAd : tuple[float,float,float], atId : int):
        atPoseXYCM = ATLocations.get_pose_by_id(atId, length=LengthType.CM)[0][:2]
        robotXYCm = robotPos2CMRAd[:2]
        return np.linalg.norm((np.subtract(atPoseXYCM,robotXYCm)))

    
    def getClosestOpen(self, robotPos2CMRAd : tuple[float,float,float], team : TEAM = None, threshold = 0.75):
        open_slots = self.getOpenSlotsAboveT(team,threshold)
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