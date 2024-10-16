import heapq
import math


class PathFinder:
    def __init__(self, map_size_x, map_size_y):
        self.start = None
        self.goal = None
        self.obstacles = set()  # Store blocked points
        self.max_path_length = 20
        self.path = []
        self.map_size_y = map_size_y
        self.map_size_x = map_size_x

    def update_values(self, start=None, goal=None, obstacles=None, max_path_length=None):
        if start:
            self.start = start
        if goal:
            self.goal = goal
        if obstacles:
            self.obstacles = self.compute_obstacle_points(obstacles)
        if max_path_length:
            self.max_path_length = max_path_length

    def update_path_with_values(self, start=None, goal=None, obstacles=None, max_path_length=None):
        if self.start != start or self.goal != goal or self.obstacles != obstacles or self.max_path_length != max_path_length:
            self.update_values(start, goal, obstacles, max_path_length)
            self.update()

    def reset(self):
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
                    if math.sqrt(dx ** 2 + dy ** 2) <= radius:
                        blocked_points.add(point)
        return blocked_points

    def a_star_search(self, start, goal, obstacles, map_size_x, map_size_y):
        open_set = []
        heapq.heappush(open_set, (0, start))
        came_from = {}
        g_score = {start: 0}
        f_score = {start: self.heuristic(start, goal)}
        step_count = 0

        while open_set:
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
            neighbors = [(0, 1), (1, 0), (0, -1), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)]

            for dx, dy in neighbors:
                neighbor = (current[0] + dx, current[1] + dy)

                # Check if the neighbor is a blocked point (within any obstacle's radius)
                if 0 <= neighbor[0] < map_size_x and 0 <= neighbor[1] < map_size_y and neighbor not in obstacles:
                    tentative_g_score = g_score[current] + 1
                    if neighbor not in g_score or tentative_g_score < g_score[neighbor]:
                        came_from[neighbor] = current
                        g_score[neighbor] = tentative_g_score
                        f_score[neighbor] = tentative_g_score + self.heuristic(neighbor, goal)
                        heapq.heappush(open_set, (f_score[neighbor], neighbor))

        return []

    def update(self):
        if self.start and self.goal:
            self.path = self.a_star_search(self.start, self.goal, self.obstacles, self.map_size_x, self.map_size_y)
            if not self.path:
                print("No path found or path exceeded maximum length.")
