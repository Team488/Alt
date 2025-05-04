# import os
# import sys
# import time
# from typing import Any, Optional, Union

# import cv2

# import numpy as np
# import pathplanning.utils as pathPlanningUtils
# from mapinternals.KalmanCache import KalmanCache
# from mapinternals.KalmanEntry import KalmanEntry
# from mapinternals.probmap import ProbMap
# from pathplanning import AStarGrid
# from pathplanning.AStarGrid import AStarPathfinder
# from pathplanning.PathFind import PathFinder
# from tools import UnitConversion
# from tools.Constants import Landmarks, MapConstants


# class PathGenerator:
#     def __init__(self, probmap: ProbMap, staticObstacleMap) -> None:
#         self.map = probmap
#         self.obstacleMap = staticObstacleMap
#         width = MapConstants.robotWidth.getCM()
#         height = MapConstants.robotHeight.getCM()
#         gridWidth, gridHeight = self.map.getInternalSizeCR()
#         self.pathFinder = AStarPathfinder(
#             self.obstacleMap, width, height, gridWidth, gridHeight, self.map.resolution
#         )

#     def generateToPointWStaticRobotsL(
#         self, currentPosition, target: Landmarks
#     ) -> Optional[list[tuple[int, int]]]:
#         return self.generateWStaticRobots(currentPosition, target.get_cm())

#     def generateToPointWStaticRobots(
#         self, currentPosition, target
#     ) -> Optional[list[tuple[int, int]]]:
#         return self.generateWStaticRobots(currentPosition, target)

#     def generateWStaticRobots(
#         self, start, goal, threshold=0.5
#     ) -> Optional[list[tuple[int, int]]]:
#         robotobstacles = self.map.getAllObjectsAboveThreshold(
#             class_idx=0, threshold=threshold
#         )
#         robotObstacleMap = np.zeros_like(self.map.getMap(class_idx=0), dtype=np.uint8)
#         for obstacle in robotobstacles:
#             cv2.circle(
#                 robotObstacleMap,
#                 (
#                     int(obstacle[0] / self.map.resolution),
#                     int(obstacle[1] / self.map.resolution),
#                 ),
#                 10,
#                 (255),
#                 -1,
#             )
#         path = self.generate(start, goal, np.fliplr(robotObstacleMap > 1))  # m to cm
#         return path

#     def generateToPointL(
#         self, currentPosition, target: Landmarks
#     ) -> Optional[list[tuple[int, int]]]:
#         return self.generate(currentPosition, target.get_cm())

#     def generateToPoint(
#         self, currentPosition, target
#     ) -> Optional[list[tuple[int, int]]]:
#         return self.generate(currentPosition, target)

#     def generate(
#         self,
#         start: tuple[Union[int, float], Union[int, float]],
#         goal: tuple[Union[int, float], Union[int, float]],
#         extraObstacles: Any = None,
#         reducePoints=True,
#     ) -> Optional[list[tuple[int, int]]]:
#         if len(start) > 2 or len(goal) > 2:
#             print(f"{start=} {goal=}")
#             print("Start and goal invalid length!!")
#             return None
#         # flipping col,row into standard row,col
#         start_arr = np.array(start)
#         goal_arr = np.array(goal)

#         # grid based so need integers
#         # reducing to internal scale
#         start_scaled = list(map(int, start_arr / self.map.resolution))
#         goal_scaled = list(map(int, goal_arr / self.map.resolution))

#         stime = time.time()
#         path = self.pathFinder.a_star_search(start_scaled, goal_scaled, extraObstacles)
#         etime = time.time()
#         print(f"Time elapsed === {(etime-stime)*1000:2f}")
#         if path is not None:
#             if reducePoints:
#                 path = self.greedy_simplify(path, 0.3)
#             return [
#                 (coord[0] * self.map.resolution, coord[1] * self.map.resolution)
#                 for coord in path
#             ]
#         return None

#     def estimateTimeToPoint(
#         self, cur, point, expectedMaxSpeed=MapConstants.RobotMaxVelocity.value
#     ):
#         linearDist = np.linalg.norm(cur, point)
#         return linearDist / expectedMaxSpeed

#     def distance_from_line(self, point, line_start, line_end):
#         # Calculate perpendicular distance from a point to a line defined by line_start and line_end
#         line_vec = np.array(line_end) - np.array(line_start)
#         point_vec = np.array(point) - np.array(line_start)
#         line_length = np.linalg.norm(line_vec)
#         if line_length == 0:  # Avoid division by zero
#             return np.linalg.norm(point_vec)
#         projection = np.dot(point_vec, line_vec) / line_length
#         closest_point = line_start + projection * line_vec / line_length
#         return np.linalg.norm(np.array(point) - closest_point)

#     def greedy_simplify(self, points, epsilon):
#         simplified = [points[0]]  # Always keep the first point
#         for i in range(1, len(points) - 1):
#             prev = simplified[-1]
#             next_point = points[i + 1]
#             # Check if the current point is close enough to the line
#             if self.distance_from_line(points[i], prev, next_point) > epsilon:
#                 simplified.append(points[i])
#         simplified.append(points[-1])  # Always keep the last point
#         return simplified
