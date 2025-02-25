import heapq
import math

import numpy as np


class PathFinder:
    def __init__(self, map_size_x, map_size_y) -> None:
        self.start = None
        self.goal = None
        self.obstacles = set()  # Store blocked points
        self.max_path_length = 20
        self.path = []
        self.map_size_y = map_size_y
        self.map_size_x = map_size_x

    def willObjectCollideWithRobot(
        P_A0, V_A, S_A, P_B0, V_B, S_B, t_max, d_min, inches_per_point
    ):
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
                return True, t, collision_position, distance
        return False, None, None, None

    def mark_collision_zone_on_grid(
        grid, P_B_predicted, d_min, inches_per_point
    ) -> None:
        radius = int(d_min / inches_per_point)
        x_center, y_center = int(P_B_predicted[0]), int(P_B_predicted[1])

        for x in range(x_center - radius, x_center + radius + 1):
            for y in range(y_center - radius, y_center + radius + 1):
                if (x - x_center) ** 2 + (y - y_center) ** 2 <= radius**2:
                    if 0 <= x < len(grid) and 0 <= y < len(grid[0]):
                        grid[x][y] = 1  # Mark the cell as an obstacle

    def update_values(
        self, start=None, goal=None, obstacles=None, max_path_length=None
    ) -> None:
        if start:
            self.start = start
        if goal:
            self.goal = goal
        if obstacles:
            self.obstacles = self.compute_obstacle_points(obstacles)
        if max_path_length:
            self.max_path_length = max_path_length

    def update_path_with_values(
        self, start=None, goal=None, obstacles=None, max_path_length=None
    ) -> None:
        if (
            self.start != start
            or self.goal != goal
            or self.obstacles != obstacles
            or self.max_path_length != max_path_length
        ):
            self.update_values(start, goal, obstacles, max_path_length)
            self.update()

    def reset(self) -> None:
        self.start = None
        self.goal = None
        self.path = []
        self.obstacles = []

    def heuristic(self, a, b):
        # Using diagonal distance heuristic
        D = 1
        D2 = 1.414
        dx = abs(a[0] - b[0])
        dy = abs(a[1] - b[1])
        return D * (dx + dy) + (D2 - 2 * D) * min(dx, dy)

    def compute_obstacle_points(self, obstacles):
        blocked_points = set()
        for obs_x, obs_y, radius, _ in obstacles:
            # Iterate over all points in a square bounding box around the obstacle
            for dx in range(-radius, radius + 1):
                for dy in range(-radius, radius + 1):
                    point = (obs_x + dx, obs_y + dy)
                    # Check if the point is inside the obstacle's radius
                    if math.sqrt(dx**2 + dy**2) <= radius:
                        blocked_points.add(point)
        return blocked_points

    def a_star_search(self, start, goal, obstacles, map_size_x, map_size_y):
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        step_count = 0

        # Calculate target direction unit vector
        target_dir = (goal[0] - start[0], goal[1] - start[1])
        target_magnitude = math.sqrt(target_dir[0] ** 2 + target_dir[1] ** 2)
        target_dir = (
            target_dir[0] / target_magnitude,
            target_dir[1] / target_magnitude,
        )

        while open_set:
            print(step_count)
            current = heapq.heappop(open_set)[1]

            # Check if we've reached the goal or exceeded the max path length
            if current == goal or step_count >= self.max_path_length:
                path = []
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
                    move_dir = (dx, dy)
                    move_magnitude = math.sqrt(move_dir[0] ** 2 + move_dir[1] ** 2)
                    move_dir = (
                        move_dir[0] / move_magnitude,
                        move_dir[1] / move_magnitude,
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
