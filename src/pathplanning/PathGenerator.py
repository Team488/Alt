import time
import numpy as np
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from mapinternals.CentralProcessor import CentralProcessor
from mapinternals.KalmanCache import KalmanCache
from mapinternals.KalmanEntry import KalmanEntry
from tools.Constants import MapConstants
from pathplanning.PathFind import PathFinder
import pathplanning.utils as pathPlanningUtils
from pathplanning import AStarGrid


class PathGenerator:
    def __init__(self, centralProcess: CentralProcessor):
        self.centralProcess = centralProcess
        pass

    def generate(
        self, start, goal, minHeightCm, customObstacleMap=None, reducePoints=False
    ):
        if len(start) > 2 or len(goal) > 2:
            print(f"{start=} {goal=}")
            print("Start and goal invalid length!!")
            return None
        obstacleMap = self.centralProcess.obstacleMap
        if customObstacleMap is not None:
            obstacleMap = np.minimum(obstacleMap, customObstacleMap)
        internal_height,internal_width = self.centralProcess.map.getInternalSize()
        # flipping col,row into standard row,col
        start = np.flip(start)
        goal = np.flip(goal)
        # reducing to internal scale
        start = tuple(map(int,start/self.centralProcess.map.resolution))
        goal = tuple(map(int,goal/self.centralProcess.map.resolution))
        
        stime = time.time()
        path = AStarGrid.a_star_search(
            obstacleMap,
            start,
            goal,
            minHeightCm,
            internal_height,
            internal_width,
        )
        etime = time.time()
        print(f"Time elapsed === {(etime-stime)*1000:2f}")
        if path is not None:
            if reducePoints:
                path = self.reduce_path(path)
            return [coord * self.centralProcess.map.resolution for coord in path]
        return None
    def estimateTimeToPoint(
        self, cur, point, expectedMaxSpeed=MapConstants.RobotMaxVelocity.value
    ):
        linearDist = np.linalg.norm(cur, point)
        return linearDist / expectedMaxSpeed

    def reduce_path(self, path):
        reduced_path = path[::2]
        return reduced_path
