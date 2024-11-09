import numpy as np
import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from mapinternals.CentralProcessor import CentralProcessor
from mapinternals.KalmanCache import KalmanCache
from mapinternals.KalmanEntry import KalmanEntry
from tools.Constants import MapConstants
from pathplanning.PathFind import PathFinder
import pathplanning.utils as pathPlanningUtils


class PathGenerator:
    def __init__(self, centralProcess: CentralProcessor):
        self.pathFinder = PathFinder(
            centralProcess.map.width, centralProcess.map.height
        )
        self.centralProcess = centralProcess
        pass

    def generate(self, start, threshold=0.7):

        robots = self.centralProcess.map.getAllRobotsAboveThreshold(threshold)
        gampieces = self.centralProcess.map.getAllGameObjectsAboveThreshold(threshold)

        best_target = pathPlanningUtils.getBestTarget(robots, gampieces, start)
        if best_target is None:
            return None

        linearTimeSeconds = self.estimateTimeToPoint(start, best_target)
        obstacles = self.__generateObstacles(
            linearTimeSeconds, self.centralProcess.kalmanCacheRobots
        )
        self.pathFinder.update_path_with_values(
            start=start,
            goal=best_target,
            obstacles=obstacles,
            max_path_length=MapConstants.fieldHeight + MapConstants.fieldWidth,
        )
        return self.pathFinder.path

    def __generateObstacles(self, timeSeconds, kalmanCacheRobots: KalmanCache):
        obstacles = []
        robotHalfW = MapConstants.robotWidth / 2
        robotHalfH = MapConstants.robotHeight / 2
        offset = (robotHalfW, robotHalfH)
        for key in kalmanCacheRobots.getKeySet():
            entry: KalmanEntry = kalmanCacheRobots.getSavedKalmanData(key)
            cur = entry[:2]
            pred = cur + entry[2:] * timeSeconds
            p1 = np.subtract(cur, offset)
            p2 = np.add(cur, offset)

            p3 = np.add(pred, offset)
            p4 = np.subtract(pred, offset)

            obstcX = (p1, p2, p3, p4)
            obstacles.append(obstcX)

        return obstacles

    def estimateTimeToPoint(
        self, cur, point, expectedMaxSpeed=MapConstants.RobotMaxVelocity
    ):
        linearDist = np.linalg.norm(cur, point)
        return linearDist / expectedMaxSpeed
