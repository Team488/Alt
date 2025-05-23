import time

import cv2
import numpy as np
import cupy as cp
import skfmm
import matplotlib.pyplot as plt
import zmq
from matplotlib.colors import LinearSegmentedColormap
import json
import BezierCurve_pb2 as BezierCurve
import JXTABLES.XTableValues_pb2 as XTableValues


class FastMarchingPathfinder:
    def __init__(self, grid_cost) -> None:
        """
        grid_cost: 2D numpy array of base traversal costs.
                   Free cells: cost 1; obstacles: higher cost (e.g., 30, 100, 1000).
                   All values must be > 0.
        """
        self.grid_cost = grid_cost.copy()
        self.height, self.width = grid_cost.shape

    def compute_time_map(self, goal):
        """
        Compute the travel time (cost-to-go) from every cell to the goal using the Fast Marching Method.
        The speed function is defined as the reciprocal of grid_cost.
        """
        speed = 1.0 / self.grid_cost  # higher cost => lower speed
        phi = np.ones_like(self.grid_cost)
        goal_x, goal_y = goal
        phi[goal_y, goal_x] = -1
        time_map = skfmm.travel_time(phi, speed)
        return time_map

    def next_step(self, pos, time_map):
        """
        Given current position pos, return the neighbor (8-neighbors) with the lowest travel time.
        """
        x, y = pos
        best = pos
        best_time = time_map[y, x]
        for dx, dy in [
            (-1, 0),
            (1, 0),
            (0, -1),
            (0, 1),
            (-1, -1),
            (-1, 1),
            (1, -1),
            (1, 1),
        ]:
            nx, ny = x + dx, y + dy
            if 0 <= nx < self.width and 0 <= ny < self.height:
                if time_map[ny, nx] < best_time:
                    best_time = time_map[ny, nx]
                    best = (nx, ny)
        return best

    def bezier_curve(self, control_points, num_points=100):
        """
        Generate a Bézier curve from a list of control points.
        For 2, 3, 4, or 5 points, use the standard linear/quadratic/cubic/quartic formulas.
        For more than 5 control points, use the de Casteljau algorithm.
        """
        # Ensure all control points are NumPy arrays (floats)
        control_points = [np.array(pt, dtype=float) for pt in control_points]
        n = len(control_points)
        t_values = np.linspace(0, 1, num_points)

        if n == 2:
            # Linear Bézier (2 control points)
            curve = np.outer(1 - t_values, control_points[0]) + np.outer(
                t_values, control_points[1]
            )
        elif n == 3:
            # Quadratic Bézier (3 control points)
            p0, p1, p2 = control_points
            curve = (
                np.outer((1 - t_values) ** 2, p0)
                + np.outer(2 * (1 - t_values) * t_values, p1)
                + np.outer(t_values**2, p2)
            )
        elif n == 4:
            # Cubic Bézier (4 control points)
            p0, p1, p2, p3 = control_points
            curve = (
                np.outer((1 - t_values) ** 3, p0)
                + np.outer(3 * t_values * (1 - t_values) ** 2, p1)
                + np.outer(3 * t_values**2 * (1 - t_values), p2)
                + np.outer(t_values**3, p3)
            )
        elif n == 5:
            # Quartic Bézier (5 control points)
            p0, p1, p2, p3, p4 = control_points
            curve = (
                np.outer((1 - t_values) ** 4, p0)
                + np.outer(4 * t_values * (1 - t_values) ** 3, p1)
                + np.outer(6 * t_values**2 * (1 - t_values) ** 2, p2)
                + np.outer(4 * t_values**3 * (1 - t_values), p3)
                + np.outer(t_values**4, p4)
            )
        else:
            # For any number > 5, use the de Casteljau algorithm.
            curve_points = []
            for tt in t_values:
                pts = control_points.copy()
                for r in range(1, n):
                    pts = [
                        (1 - tt) * pts[i] + tt * pts[i + 1] for i in range(len(pts) - 1)
                    ]
                curve_points.append(pts[0])
            curve = np.array(curve_points)
        return curve

    def check_collision(self, curve):
        """
        Check if any point along the curve collides with an obstacle.
        """
        xs = np.rint(curve[:, 0]).astype(int)
        ys = np.rint(curve[:, 1]).astype(int)
        valid = (xs >= 0) & (xs < self.width) & (ys >= 0) & (ys < self.height)
        xs, ys = xs[valid], ys[valid]
        return np.any(self.grid_cost[ys, xs] >= 100)

    def try_inflate_segment(
        self, segment, max_offset_pixels=45, tol=1.0, record_history=False
    ):
        """
        Try to inflate (bend) a segment using a binary search on the perpendicular offset
        so that the resulting Bézier curve avoids collisions.

        Instead of stopping after the first safe candidate is found, this version
        continues for both search directions and collects all binary search iterations.

        If record_history is True, each iteration's parameters and results are recorded.

        Returns:
            If record_history:
                (best_candidate, combined_history) where combined_history is a list of tuples:
                  (mid_offset, mid_point, candidate_curve, collision)
            Otherwise:
                best_candidate (or None if inflation fails)
        """
        if len(segment) < 2:
            return None if not record_history else (None, [])

        p0 = np.array(segment[0], dtype=float)
        p_end = np.array(segment[-1], dtype=float)
        chord = p_end - p0
        chord_length = np.linalg.norm(chord)
        if chord_length == 0:
            return None if not record_history else (None, [])

        perp = np.array([-chord[1], chord[0]]) / chord_length
        combined_history = [] if record_history else None
        candidate_list = []

        # Try both directions.
        for sign in [1, -1]:
            lower, upper = 0, max_offset_pixels  # Reset bounds for this sign.
            history_dir = [] if record_history else None
            best_candidate_dir = None

            while upper - lower > tol:
                mid_offset = (lower + upper) / 2.0
                mid = (p0 + p_end) / 2 + sign * perp * mid_offset
                candidate_segment = [segment[0], tuple(mid), segment[-1]]
                candidate_curve = self.bezier_curve(candidate_segment, num_points=100)
                collision = self.check_collision(candidate_curve)
                if record_history:
                    history_dir.append(
                        (mid_offset, mid.copy(), candidate_curve.copy(), collision)
                    )
                if not collision:
                    best_candidate_dir = candidate_segment
                    upper = mid_offset  # Try a smaller offset.
                else:
                    lower = mid_offset  # Increase offset.
            if record_history:
                combined_history.extend(history_dir)
            if best_candidate_dir is not None:
                candidate_list.append(best_candidate_dir)

        if candidate_list:
            # Choose the candidate with the smallest offset from the chord's midpoint.
            def candidate_offset(candidate):
                mid = np.array(candidate[1])
                return np.linalg.norm(mid - (p0 + p_end) / 2)

            best_candidate = min(candidate_list, key=candidate_offset)
            if record_history:
                return best_candidate, combined_history
            else:
                return best_candidate

        if record_history:
            return None, combined_history
        return None

    def generate_safe_bezier_paths(self, control_points):
        """
        Build segments of Bézier curves from control_points.
        Instead of immediately splitting a segment when a collision is detected, try to inflate
        the segment to avoid the obstacle. If inflation fails, then split the segment.

        Returns:
            final_segments (list of np.ndarray): Each element is an array of control points for the segment.
        """
        segments = []
        segment = [control_points[0]]
        for i in range(1, len(control_points)):
            segment.append(control_points[i])
            curve = self.bezier_curve(segment, num_points=100)
            if self.check_collision(curve):
                inflated_segment = self.try_inflate_segment(segment)
                if inflated_segment is not None:
                    segment = inflated_segment
                    curve = self.bezier_curve(segment, num_points=100)
                    if self.check_collision(curve):
                        segments.append(segment[:-1])
                        segment = [control_points[i - 1], control_points[i]]
                else:
                    segments.append(segment[:-1])
                    segment = [control_points[i - 1], control_points[i]]
        segments.append(segment)
        final_segments = [np.array(seg) for seg in segments]
        return final_segments


def deflate_inflection_points(points, distance_threshold=2.0):
    """
    Reduce the number of control points by averaging clusters of points that are
    within a specified distance threshold from one another.
    """
    if not points:
        return []
    group = [np.array(points[0], dtype=float)]
    deflated_points = []
    for pt in points[1:]:
        pt = np.array(pt, dtype=float)
        if np.linalg.norm(pt - group[-1]) <= distance_threshold:
            group.append(pt)
        else:
            avg_point = np.mean(group, axis=0)
            deflated_points.append(tuple(avg_point))
            group = [pt]
    if group:
        avg_point = np.mean(group, axis=0)
        deflated_points.append(tuple(avg_point))
    return deflated_points


def get_static_obstacles(filename):
    """
    Load static obstacle coordinates from a JSON file.
    The JSON file should contain a list of [x, y] coordinates.
    Returns a list of [x, y] pairs.
    """
    with open(filename, "r") as f:
        obstacles = json.load(f)
    return obstacles


def apply_and_inflate_all_obstacles(
    grid, static_obs_array, dynamic_obs_array, safe_distance
):
    """
    Applies both static and dynamic obstacles (with inflation) onto the grid,
    ensuring that inflated obstacles do not go out of bounds.
    """
    # --- Apply static obstacles ---
    for coord in static_obs_array:
        x, y = coord
        if 0 <= x < grid.shape[1] and 0 <= y < grid.shape[0]:
            grid[y, x] = 100000
    # Inflate static obstacles using dilation.
    binary_static = (grid > 1).astype(np.uint8)
    kernel_size = int(safe_distance)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    inflated_static = cv2.dilate(binary_static, kernel, iterations=1)
    grid[inflated_static == 1] = 100000
    # --- Apply dynamic obstacles ---
    for obs in dynamic_obs_array:
        cx, cy, heat, size = obs
        mask = np.zeros_like(grid, dtype=np.uint8)
        x_min = max(0, int(np.floor(cx - size)))
        x_max = min(grid.shape[1] - 1, int(np.ceil(cx + size)))
        y_min = max(0, int(np.floor(cy - size)))
        y_max = min(grid.shape[0] - 1, int(np.ceil(cy + size)))
        for x in range(x_min, x_max + 1):
            for y in range(y_min, y_max + 1):
                if (x - cx) ** 2 + (y - cy) ** 2 <= size**2:
                    mask[y, x] = 1
        kernel_dynamic_size = int(size) + 1
        kernel_dynamic = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (kernel_dynamic_size, kernel_dynamic_size)
        )
        inflated_mask = cv2.dilate(mask, kernel_dynamic, iterations=1)
        indices = np.argwhere(inflated_mask == 1)
        for y, x in indices:
            if 0 <= x < grid.shape[1] and 0 <= y < grid.shape[0]:
                grid[y, x] = heat
    return grid


def find_inflection_points(path):
    """
    Extract inflection points from the path (points where the direction changes).
    """
    if len(path) < 3:
        return path
    inflection_points = [path[0]]
    for i in range(1, len(path) - 1):
        prev_dx = path[i][0] - path[i - 1][0]
        prev_dy = path[i][1] - path[i - 1][1]
        next_dx = path[i + 1][0] - path[i][0]
        next_dy = path[i + 1][1] - path[i][1]
        if (prev_dx, prev_dy) != (next_dx, next_dy):
            inflection_points.append(path[i])
    inflection_points.append(path[-1])
    return inflection_points


def build_bezier_curves_proto(final_segments):
    """
    Build a BezierCurves protobuf from the final path segments and their traversal times.

    Args:
        final_segments: Either a NumPy array or a list of NumPy arrays. The array can be:
                        - 2D array of shape (N, 2) representing a single segment, or
                        - 3D array of shape (num_segments, N, 2) for multiple segments, or
                        - a list of 2D arrays.

    Returns:
        your_proto_pb2.BezierCurves: The populated protobuf message.
    """
    # Create the top-level BezierCurves message
    bezier_curves_msg = XTableValues.BezierCurves()

    # Normalize input to be an iterable of segments.
    if isinstance(final_segments, list):
        segments = final_segments
    elif isinstance(final_segments, np.ndarray):
        if final_segments.ndim == 2:
            segments = [final_segments]
        else:
            segments = final_segments
    else:
        raise TypeError("final_segments must be a list or a numpy array.")

    # Iterate through segments
    for segment in segments:
        # Create a BezierCurve entry for the current segment
        curve_msg = bezier_curves_msg.curves.add()
        # Fill in the control points for this curve
        for (x_val, y_val) in segment:
            cp = curve_msg.controlPoints.add()
            cp.x = x_val
            cp.y = y_val

    return bezier_curves_msg


def server() -> None:
    context = zmq.Context()
    socket = context.socket(zmq.REP)
    bind = "tcp://127.0.0.1:8531"
    socket.bind(bind)
    print("Server started on " + bind)
    fieldHeightMeters = 8.05
    fieldWidthMeters = 17.55
    grid_width = 690
    grid_height = 316
    ROBOT_SIZE_INCHES = 45

    PIXELS_PER_METER_X = grid_width / fieldWidthMeters
    PIXELS_PER_METER_Y = grid_height / fieldHeightMeters
    # POSE 2D
    while True:
        message = socket.recv()
        request = BezierCurve.PlanBezierPathRequest.FromString(message)
        start = (request.start.x, request.start.y)
        goal = (request.goal.x, request.goal.y)
        SAFE_DISTANCE_INCHES = request.safeRadiusInches
        TOTAL_SAFE_DISTANCE = ROBOT_SIZE_INCHES + SAFE_DISTANCE_INCHES

        base_grid = np.ones((grid_height, grid_width), dtype=float)
        static_obs_array = get_static_obstacles("static_obstacles_inch.json")
        dynamic_obs_array = []
        combined_grid = apply_and_inflate_all_obstacles(
            base_grid.copy(), static_obs_array, dynamic_obs_array, TOTAL_SAFE_DISTANCE
        )
        pathfinder = FastMarchingPathfinder(combined_grid)
        START = (int(start[0] * PIXELS_PER_METER_X), int(start[1] * PIXELS_PER_METER_Y))
        GOAL = (int(goal[0] * PIXELS_PER_METER_X), int(goal[1] * PIXELS_PER_METER_Y))
        time_map = pathfinder.compute_time_map(GOAL)
        path = [START]
        current = START
        max_steps = 10000
        for _ in range(max_steps):
            next_cell = pathfinder.next_step(current, time_map)
            if next_cell == current:
                break  # No progress: local minimum reached.
            path.append(next_cell)
            current = next_cell
            if current == goal:
                break
        inflection_points = find_inflection_points(path)
        smoothed_control_points = deflate_inflection_points(inflection_points)

        safe_bezier_segments = pathfinder.generate_safe_bezier_paths(
            smoothed_control_points
        )
        safe_bezier_segments_poses = [
            segment / np.array([PIXELS_PER_METER_X, PIXELS_PER_METER_Y])
            for segment in safe_bezier_segments
        ]
        response = build_bezier_curves_proto(safe_bezier_segments_poses)
        socket.send(response.SerializeToString(), zmq.DONTWAIT)


if __name__ == "__main__":
    server()
