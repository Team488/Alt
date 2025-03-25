import os
import sys
import time
from typing import Any, Optional, Union

import cv2

import numpy as np
import pathplanning.utils as pathPlanningUtils
from mapinternals.KalmanCache import KalmanCache
from mapinternals.KalmanEntry import KalmanEntry
from mapinternals.probmap import ProbMap
from pathplanning import AStarGrid
from pathplanning.AStarGrid import AStarPathfinder
from pathplanning.PathFind import PathFinder
from tools import UnitConversion
from tools.Constants import Landmarks, MapConstants

"""
Path generation system for robot navigation with obstacle avoidance.

This module provides a higher-level path generation system built on top of
the A* pathfinding algorithm. It handles coordinate transformations between
world space and grid space, integrates with the probabilistic map system, and
implements path simplification to reduce unnecessary waypoints.
"""

class PathGenerator:
    """
    High-level path planning system with obstacle avoidance.
    
    This class provides methods for generating paths between points while
    avoiding both static obstacles and dynamically detected robots. It works
    with the probability map system to incorporate real-time obstacle information
    and supports both landmark-based and coordinate-based navigation.
    
    Attributes:
        map: Probability map containing object detection information
        obstacleMap: Static obstacle map for permanent obstacles
        pathFinder: A* pathfinding implementation 
    """
    
    def __init__(self, probmap: ProbMap, staticObstacleMap) -> None:
        """
        Initialize a new path generator with the given maps.
        
        Args:
            probmap: Probability map for object detection information
            staticObstacleMap: Static obstacle map for permanent obstacles
        """
        self.map = probmap
        self.obstacleMap = staticObstacleMap
        width = MapConstants.robotWidth.getCM()
        height = MapConstants.robotHeight.getCM()
        gridWidth, gridHeight = self.map.getInternalSizeCR()
        self.pathFinder = AStarPathfinder(
            self.obstacleMap, width, height, gridWidth, gridHeight, self.map.resolution
        )

    def generateToPointWStaticRobotsL(
        self, currentPosition, target: Landmarks
    ) -> Optional[list[tuple[int, int]]]:
        """
        Generate a path to a landmark while avoiding static robots.
        
        Convenience method that converts a landmark to its coordinates and
        calls the main path generation method.
        
        Args:
            currentPosition: Starting position (x, y) in world units
            target: Landmark enum value representing the destination
            
        Returns:
            List of waypoints as (x, y) coordinates, or None if no path is found
        """
        return self.generateWStaticRobots(currentPosition, target.get_cm())

    def generateToPointWStaticRobots(
        self, currentPosition, target
    ) -> Optional[list[tuple[int, int]]]:
        """
        Generate a path to coordinates while avoiding static robots.
        
        Args:
            currentPosition: Starting position (x, y) in world units
            target: Destination position (x, y) in world units
            
        Returns:
            List of waypoints as (x, y) coordinates, or None if no path is found
        """
        return self.generateWStaticRobots(currentPosition, target)

    def generateWStaticRobots(
        self, start, goal, threshold=0.5
    ) -> Optional[list[tuple[int, int]]]:
        """
        Generate a path avoiding both static obstacles and detected robots.
        
        This method:
        1. Gets all robot detections above the probability threshold
        2. Creates a temporary obstacle map with these robots
        3. Calls the main path generation method with this combined map
        
        Args:
            start: Starting position (x, y) in world units
            goal: Destination position (x, y) in world units
            threshold: Probability threshold for considering robot detections (0-1)
            
        Returns:
            List of waypoints as (x, y) coordinates, or None if no path is found
        """
        robotobstacles = self.map.getAllObjectsAboveThreshold(
            class_idx=0, threshold=threshold
        )
        robotObstacleMap = np.zeros_like(self.map.getMap(class_idx=0), dtype=np.uint8)
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

    def generateToPointL(
        self, currentPosition, target: Landmarks
    ) -> Optional[list[tuple[int, int]]]:
        """
        Generate a path to a landmark while avoiding static obstacles.
        
        Convenience method that converts a landmark to its coordinates and
        calls the main path generation method.
        
        Args:
            currentPosition: Starting position (x, y) in world units
            target: Landmark enum value representing the destination
            
        Returns:
            List of waypoints as (x, y) coordinates, or None if no path is found
        """
        return self.generate(currentPosition, target.get_cm())

    def generateToPoint(
        self, currentPosition, target
    ) -> Optional[list[tuple[int, int]]]:
        """
        Generate a path to coordinates while avoiding static obstacles.
        
        Args:
            currentPosition: Starting position (x, y) in world units
            target: Destination position (x, y) in world units
            
        Returns:
            List of waypoints as (x, y) coordinates, or None if no path is found
        """
        return self.generate(currentPosition, target)

    def generate(
        self,
        start: tuple[Union[int, float], Union[int, float]],
        goal: tuple[Union[int, float], Union[int, float]],
        extraObstacles: Any = None,
        reducePoints=True,
    ) -> Optional[list[tuple[int, int]]]:
        """
        Core path generation method - converts coordinates and runs A* search.
        
        This is the main implementation method that:
        1. Validates the input coordinates
        2. Converts from world coordinates to grid coordinates
        3. Runs the A* search algorithm
        4. Optionally simplifies the resulting path
        5. Converts back to world coordinates
        
        Args:
            start: Starting position (x, y) in world units
            goal: Destination position (x, y) in world units
            extraObstacles: Additional obstacle map to consider (e.g., for dynamic obstacles)
            reducePoints: Whether to simplify the path by removing unnecessary waypoints
            
        Returns:
            List of waypoints as (x, y) coordinates in world units, or None if no path is found
        """
        if len(start) > 2 or len(goal) > 2:
            print(f"{start=} {goal=}")
            print("Start and goal invalid length!!")
            return None
        # flipping col,row into standard row,col
        start_arr = np.array(start)
        goal_arr = np.array(goal)

        # grid based so need integers
        # reducing to internal scale
        start_scaled = list(map(int, start_arr / self.map.resolution))
        goal_scaled = list(map(int, goal_arr / self.map.resolution))

        stime = time.time()
        path = self.pathFinder.a_star_search(start_scaled, goal_scaled, extraObstacles)
        etime = time.time()
        print(f"Time elapsed === {(etime-stime)*1000:2f}")
        if path is not None:
            if reducePoints:
                path = self.greedy_simplify(path, 0.3)
            return [
                (coord[0] * self.map.resolution, coord[1] * self.map.resolution)
                for coord in path
            ]
        return None

    def estimateTimeToPoint(
        self, cur, point, expectedMaxSpeed=MapConstants.RobotMaxVelocity.value
    ):
        """
        Estimate the time to reach a point given the robot's maximum speed.
        
        Uses a simple linear distance / speed calculation.
        
        Args:
            cur: Current position
            point: Target position
            expectedMaxSpeed: Maximum velocity of the robot in distance units per second
            
        Returns:
            Estimated time in seconds to reach the target
        """
        linearDist = np.linalg.norm(cur, point)
        return linearDist / expectedMaxSpeed

    def distance_from_line(self, point, line_start, line_end):
        """
        Calculate the perpendicular distance from a point to a line segment.
        
        Used in path simplification to determine which points can be safely
        removed without significantly altering the path.
        
        Args:
            point: The point to check
            line_start: Start point of the line segment
            line_end: End point of the line segment
            
        Returns:
            The perpendicular distance from the point to the line segment
        """
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
        """
        Simplify a path by removing unnecessary waypoints.
        
        Uses a greedy algorithm that removes points that are within a certain
        distance (epsilon) of the line connecting their neighbors. This reduces
        the number of waypoints while maintaining the general shape of the path.
        
        Args:
            points: List of (x, y) coordinates representing the path
            epsilon: Maximum distance a point can be from the line to be removed
            
        Returns:
            Simplified path as a list of (x, y) coordinates
        """
        simplified = [points[0]]  # Always keep the first point
        for i in range(1, len(points) - 1):
            prev = simplified[-1]
            next_point = points[i + 1]
            # Check if the current point is close enough to the line
            if self.distance_from_line(points[i], prev, next_point) > epsilon:
                simplified.append(points[i])
        simplified.append(points[-1])  # Always keep the last point
        return simplified
