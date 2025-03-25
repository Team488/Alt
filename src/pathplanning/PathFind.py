import heapq
import math
from typing import List, Set, Tuple, Optional, Dict, Any

import numpy as np

"""
Path finding implementation with obstacle avoidance and collision detection.

This module provides a customizable path finding system using A* search algorithm
with weighted heuristics to prefer paths that align with the target direction.
It also includes utilities for collision detection and prediction.
"""

class PathFinder:
    """
    A* path finding system with obstacle avoidance.
    
    Implements a modified A* path finding algorithm that prefers paths aligned with 
    the goal direction. The system includes features for handling obstacles, 
    collision detection, and limiting maximum path length.
    
    Attributes:
        start: Starting point coordinates (x, y)
        goal: Target point coordinates (x, y)
        obstacles: Set of blocked coordinates on the map
        max_path_length: Maximum number of steps in the path (limits computation)
        path: Current computed path as list of (x, y) coordinates
        map_size_x: Width of the map in grid units
        map_size_y: Height of the map in grid units
    """
    
    def __init__(self, map_size_x: int, map_size_y: int) -> None:
        """
        Initialize a new path finder for a map of the given dimensions.
        
        Args:
            map_size_x: Width of the map in grid units
            map_size_y: Height of the map in grid units
        """
        self.start: Optional[Tuple[int, int]] = None
        self.goal: Optional[Tuple[int, int]] = None
        self.obstacles: Set[Tuple[int, int]] = set()  # Store blocked points
        self.max_path_length: int = 20
        self.path: List[Tuple[int, int]] = []
        self.map_size_y: int = map_size_y
        self.map_size_x: int = map_size_x

    @staticmethod
    def willObjectCollideWithRobot(
        P_A0: Tuple[float, float], 
        V_A: Tuple[float, float], 
        S_A: float, 
        P_B0: Tuple[float, float], 
        V_B: Tuple[float, float], 
        S_B: float, 
        t_max: float, 
        d_min: float, 
        inches_per_point: float
    ) -> Tuple[bool, Optional[float], Optional[Tuple[float, float]], Optional[float]]:
        """
        Predict if two moving objects will collide in the future.
        
        Simulates the positions of two objects moving with constant velocity over time
        and checks if they will come within a minimum safe distance of each other.
        
        Args:
            P_A0: Initial position of object A (x, y)
            V_A: Direction vector of object A (dx, dy)
            S_A: Speed of object A (magnitude)
            P_B0: Initial position of object B (x, y)
            V_B: Direction vector of object B (dx, dy)
            S_B: Speed of object B (magnitude)
            t_max: Maximum time to simulate in seconds
            d_min: Minimum safe distance between objects
            inches_per_point: Conversion from grid units to inches
            
        Returns:
            Tuple containing:
            - Boolean indicating whether collision will occur
            - Time at which collision occurs (or None)
            - Position of collision (or None)
            - Distance at collision (or None)
        """
        for t in np.linspace(0, t_max, num=1000):
            P_A_t = (P_A0[0] + V_A[0] * S_A * t, P_A0[1] + V_A[1] * S_A * t)
            P_B_t = (P_B0[0] + V_B[0] * S_B * t, P_B0[1] + V_B[1] * S_B * t)
            distance = (
                np.linalg.norm(np.array(P_A_t) - np.array(P_B_t)) * inches_per_point
            )
            if distance < d_min:
                collision_position = (
                    (P_A_t[0] + P_B_t[0]) / 2,
                    (P_A_t[1] + P_B_t[1]) / 2,
                )
                return True, float(t), (float(collision_position[0]), float(collision_position[1])), float(distance)
        return False, None, None, None

    @staticmethod
    def mark_collision_zone_on_grid(
        grid: List[List[int]], 
        P_B_predicted: Tuple[float, float], 
        d_min: float, 
        inches_per_point: float
    ) -> None:
        """
        Mark a circular zone around a predicted collision point as obstacles.
        
        Creates a circular region of obstacle cells on the grid centered around
        the predicted collision point, with a radius determined by the minimum safe distance.
        
        Args:
            grid: The grid to mark obstacles on (modified in-place)
            P_B_predicted: Center point of collision (x, y)
            d_min: Minimum safe distance in inches
            inches_per_point: Conversion from grid units to inches
        """
        radius = int(d_min / inches_per_point)
        x_center, y_center = int(P_B_predicted[0]), int(P_B_predicted[1])

        for x in range(x_center - radius, x_center + radius + 1):
            for y in range(y_center - radius, y_center + radius + 1):
                if (x - x_center) ** 2 + (y - y_center) ** 2 <= radius**2:
                    if 0 <= x < len(grid) and 0 <= y < len(grid[0]):
                        grid[x][y] = 1  # Mark the cell as an obstacle

    def update_values(
        self, 
        start: Optional[Tuple[int, int]] = None, 
        goal: Optional[Tuple[int, int]] = None, 
        obstacles: Optional[List[Tuple[int, int, int, Any]]] = None, 
        max_path_length: Optional[int] = None
    ) -> None:
        """
        Update the path finder's key parameters.
        
        Updates only the parameters that are provided, leaving others unchanged.
        When obstacles are updated, they are converted to grid points.
        
        Args:
            start: New starting position (x, y) or None to keep current
            goal: New goal position (x, y) or None to keep current
            obstacles: List of obstacle definitions or None to keep current
            max_path_length: New maximum path length or None to keep current
        """
        if start:
            self.start = start
        if goal:
            self.goal = goal
        if obstacles:
            self.obstacles = self.compute_obstacle_points(obstacles)
        if max_path_length:
            self.max_path_length = max_path_length

    def update_path_with_values(
        self, 
        start: Optional[Tuple[int, int]] = None, 
        goal: Optional[Tuple[int, int]] = None, 
        obstacles: Optional[List[Tuple[int, int, int, Any]]] = None, 
        max_path_length: Optional[int] = None
    ) -> None:
        """
        Update parameters and recalculate path if anything has changed.
        
        This is a convenience method that only triggers path recalculation
        if any of the input parameters differ from the current values.
        
        Args:
            start: New starting position (x, y) or None to keep current
            goal: New goal position (x, y) or None to keep current
            obstacles: List of obstacle definitions or None to keep current
            max_path_length: New maximum path length or None to keep current
        """
        if (
            self.start != start
            or self.goal != goal
            or self.obstacles != obstacles
            or self.max_path_length != max_path_length
        ):
            self.update_values(start, goal, obstacles, max_path_length)
            self.update()

    def reset(self) -> None:
        """
        Reset the path finder to its initial state.
        
        Clears the start and goal positions, resets the path to empty,
        and removes all obstacles.
        """
        self.start = None
        self.goal = None
        self.path = []
        self.obstacles = set()  # Changed from [] to set() to match declaration

    def heuristic(self, a: Tuple[int, int], b: Tuple[int, int]) -> float:
        """
        Calculate the heuristic distance between two points.
        
        Uses a diagonal distance heuristic which is an admissible heuristic
        for grid-based pathfinding with diagonal movement. This heuristic
        properly accounts for the increased cost of diagonal movement.
        
        Args:
            a: First point coordinates (x, y)
            b: Second point coordinates (x, y)
            
        Returns:
            Estimated distance between the points
        """
        # Using diagonal distance heuristic
        D = 1
        D2 = 1.414  # Approximate sqrt(2) for diagonal movement cost
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return D * (dx + dy) + (D2 - 2 * D) * min(dx, dy)

    def compute_obstacle_points(self, obstacles: List[Tuple[int, int, int, Any]]) -> Set[Tuple[int, int]]:
        """
        Convert obstacle descriptions to a set of grid points.
        
        Takes a list of obstacles defined by their center point and radius,
        and converts them to a set of individual grid points that should be
        considered blocked for pathfinding.
        
        Args:
            obstacles: List of (x, y, radius, metadata) tuples defining obstacles
            
        Returns:
            Set of (x, y) coordinates that are blocked by obstacles
        """
        blocked_points: Set[Tuple[int, int]] = set()
        for obs_x, obs_y, radius, _ in obstacles:
            # Iterate over all points in a square bounding box around the obstacle
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    point = (obs_x + dx, obs_y + dy)
                    # Check if the point is inside the obstacle's radius
                    if math.sqrt(dx**2 + dy**2) <= radius:
                        blocked_points.add(point)
        return blocked_points

    def a_star_search(
        self, 
        start: Tuple[int, int], 
        goal: Tuple[int, int], 
        obstacles: Set[Tuple[int, int]], 
        map_size_x: int, 
        map_size_y: int
    ) -> List[Tuple[int, int]]:
        """
        Execute the A* search algorithm to find an optimal path.
        
        Implements a modified A* algorithm that includes:
        - Direction-based cost weighting to prefer paths aligned with the goal
        - Support for diagonal movement
        - Integration with the obstacle system
        - Path length limiting to avoid excessive computation
        
        Args:
            start: Starting position coordinates (x, y)
            goal: Goal position coordinates (x, y)
            obstacles: Set of grid coordinates that are blocked
            map_size_x: Width of the map in grid units
            map_size_y: Height of the map in grid units
            
        Returns:
            Ordered list of (x, y) coordinates representing the path from
            start to goal, or an empty list if no path is found
        """
        open_set: List[Tuple[float, Tuple[int, int]]] = []
        heapq.heappush(open_set, (0, start))
        came_from: Dict[Tuple[int, int], Tuple[int, int]] = {}
        g_score: Dict[Tuple[int, int], float] = {start: 0}
        f_score: Dict[Tuple[int, int], float] = {start: self.heuristic(start, goal)}
        step_count: int = 0

        # Calculate target direction unit vector
        raw_target_dir = (goal[0] - start[0], goal[1] - start[1])
        target_magnitude = math.sqrt(raw_target_dir[0] ** 2 + raw_target_dir[1] ** 2)
        if target_magnitude > 0:  # Avoid division by zero
            target_dir = (
                float(raw_target_dir[0] / target_magnitude),
                float(raw_target_dir[1] / target_magnitude),
            )
        else:
            target_dir = (0.0, 0.0)  # Default if start and goal are the same

        while open_set:
            print(step_count)
            current = heapq.heappop(open_set)[1]

            # Check if we've reached the goal or exceeded the max path length
            if current == goal or step_count >= self.max_path_length:
                path: List[Tuple[int, int]] = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1]  # Return reversed path and cut off at max path length

            step_count += 1

            # Explore neighbors
            neighbors = [
                (0, 1),
                (1, 0),
                (0, -1),
                (-1, 0),
                (1, 1),
                (1, -1),
                (-1, 1),
                (-1, -1),
            ]

            for dx, dy in neighbors:
                neighbor = (current[0] + dx, current[1] + dy)
                move_cost = (
                    1.414 if dx != 0 and dy != 0 else 1
                )  # Base cost for diagonal and straight moves

                # Check if the neighbor is valid
                if (
                    0 <= neighbor[0] < map_size_x
                    and 0 <= neighbor[1] < map_size_y
                    and neighbor not in obstacles
                ):
                    # Calculate move direction vector
                    raw_move_dir = (dx, dy)
                    move_magnitude = math.sqrt(raw_move_dir[0] ** 2 + raw_move_dir[1] ** 2)
                    move_dir = (
                        float(raw_move_dir[0] / move_magnitude),
                        float(raw_move_dir[1] / move_magnitude),
                    )

                    # Use dot product to scale move cost
                    alignment = (move_dir[0] * target_dir[0]) + (
                        move_dir[1] * target_dir[1]
                    )
                    alignment_factor = 1.0 + (
                        1.0 - alignment
                    )  # Higher alignment => lower cost
                    scaled_cost = move_cost * alignment_factor

                    tentative_g_score = g_score[current] + scaled_cost
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self.heuristic(
                            neighbor, goal
                        )
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return []

    def update(self) -> None:
        """
        Update the path based on current start, goal, and obstacles.
        
        This method triggers a path recalculation and updates the path
        attribute with the new results. If no path can be found, it
        outputs diagnostic information to help with troubleshooting.
        
        Note: This method requires start and goal to be set before calling.
        """
        if self.start and self.goal:
            self.path = self.a_star_search(
                self.start, self.goal, self.obstacles, self.map_size_x, self.map_size_y
            )
            if not self.path:
                print("Start:", self.start)
                print("Goal:", self.goal)
                # print("Obstacles:", self.obstacles)
                print("Max Path Length:", self.max_path_length)
                print("Map Size:", (self.map_size_x, self.map_size_y))
                print("No path found or path exceeded maximum length.")
