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
        obstacleMap = self.centralProcess.obstacleMap
        if customObstacleMap is not None:
            obstacleMap = np.minimum(obstacleMap, customObstacleMap)
        path = AStarGrid.a_star_search(
            obstacleMap,
            start,
            goal,
            minHeightCm,
            self.centralProcess.map.internalHeight,
            self.centralProcess.map.internalWidth,
        )
        if path is not None and reducePoints:
            path = self.reduce_path(path)
        return path

    def estimateTimeToPoint(
        self, cur, point, expectedMaxSpeed=MapConstants.RobotMaxVelocity.value
    ):
        linearDist = np.linalg.norm(cur, point)
        return linearDist / expectedMaxSpeed

    def reduce_path(self, path):
        reduced_path = path[::2]
        return reduced_path
