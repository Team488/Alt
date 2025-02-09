import time
import numpy as np
import os
import sys
import cv2

from mapinternals.KalmanCache import KalmanCache
from mapinternals.KalmanEntry import KalmanEntry
from mapinternals.probmap import ProbMap
from tools.Constants import MapConstants
from pathplanning.PathFind import PathFinder
import pathplanning.utils as pathPlanningUtils
from pathplanning import AStarGrid
from pathplanning.AStarGrid import AStarPathfinder
from tools import UnitConversion
from tools.Constants import Landmarks


class PathGenerator:
    def __init__(self, probmap: ProbMap, staticObstacleMap):
        self.map = probmap
        self.obstacleMap = staticObstacleMap
        width = MapConstants.robotWidth.getCM()
        height = MapConstants.robotHeight.getCM()
        gridWidth, gridHeight = self.map.getInternalSizeCR()
        self.pathFinder = AStarPathfinder(
            self.obstacleMap, width, height, gridWidth, gridHeight, self.map.resolution
        )

    def generateToPointWStaticRobotsL(self, currentPosition, target: Landmarks):
        return self.generateWStaticRobots(currentPosition, target.get_cm())

    def generateToPointWStaticRobots(self, currentPosition, target):
        return self.generateWStaticRobots(currentPosition, target)

    def generateWStaticRobots(self, start, goal, threshold=0.5):
        robotobstacles = self.map.getAllRobotsAboveThreshold(threshold)
        robotObstacleMap = np.zeros_like(self.map.getRobotMap(), dtype=np.uint8)
        for obstacle in robotobstacles:
            cv2.circle(
                robotObstacleMap,
                (
                    int(obstacle[0] / self.map.resolution),
                    int(obstacle[1] / self.map.resolution),
                ),
                10,
                (255),
                -1,
            )
        path = self.generate(start, goal, np.fliplr(robotObstacleMap > 1))  # m to cm
        return path

    def generateToPointL(self, currentPosition, target: Landmarks):
        return self.generate(currentPosition, target.get_cm())

    def generateToPoint(self, currentPosition, target):
        return self.generate(currentPosition, target)

    def generate(self, start, goal, extraObstacles=None, reducePoints=True):
        if len(start) > 2 or len(goal) > 2:
            print(f"{start=} {goal=}")
            print("Start and goal invalid length!!")
            return None
        # flipping col,row into standard row,col
        start = np.array(start)
        goal = np.array(goal)

        # grid based so need integers
        # reducing to internal scale
        start = tuple(map(int, start / self.map.resolution))
        goal = tuple(map(int, goal / self.map.resolution))

        stime = time.time()
        path = self.pathFinder.a_star_search(start, goal, extraObstacles)
        etime = time.time()
        print(f"Time elapsed === {(etime-stime)*1000:2f}")
        if path is not None:
            if reducePoints:
                path = self.greedy_simplify(path, 0.3)
            return [coord * self.map.resolution for coord in path]
        return None

    def estimateTimeToPoint(
        self, cur, point, expectedMaxSpeed=MapConstants.RobotMaxVelocity.value
    ):
        linearDist = np.linalg.norm(cur, point)
        return linearDist / expectedMaxSpeed

    def distance_from_line(self, point, line_start, line_end):
        # Calculate perpendicular distance from a point to a line defined by line_start and line_end
        line_vec = np.array(line_end) - np.array(line_start)
        point_vec = np.array(point) - np.array(line_start)
        line_length = np.linalg.norm(line_vec)
        if line_length == 0:  # Avoid division by zero
            return np.linalg.norm(point_vec)
        projection = np.dot(point_vec, line_vec) / line_length
        closest_point = line_start + projection * line_vec / line_length
        return np.linalg.norm(np.array(point) - closest_point)

    def greedy_simplify(self, points, epsilon):
        simplified = [points[0]]  # Always keep the first point
        for i in range(1, len(points) - 1):
            prev = simplified[-1]
            next_point = points[i + 1]
            # Check if the current point is close enough to the line
            if self.distance_from_line(points[i], prev, next_point) > epsilon:
                simplified.append(points[i])
        simplified.append(points[-1])  # Always keep the last point
        return simplified
