import math
import time

import grpc
from concurrent import futures
from JXTABLES import XTableValues_pb2 as XTableValues
from JXTABLES import XTableValues_pb2_grpc as XTableGRPC

import cv2
import numpy as np
import skfmm
import json


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

    def check_collision(self, curve, minimum_heat=100):
        """
        Check if any point along the curve collides with an obstacle.
        """
        xs = np.rint(curve[:, 0]).astype(int)
        ys = np.rint(curve[:, 1]).astype(int)
        valid = (xs >= 0) & (xs < self.width) & (ys >= 0) & (ys < self.height)
        xs, ys = xs[valid], ys[valid]
        return np.any(self.grid_cost[ys, xs] >= minimum_heat)

    def try_inflate_segment(self, segment, max_offset_pixels=60, tol=1.0):
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
            return None

        p0 = np.array(segment[0], dtype=float)
        p_end = np.array(segment[-1], dtype=float)
        chord = p_end - p0
        chord_length = np.linalg.norm(chord)
        if chord_length == 0:
            return None

        perp = np.array([-chord[1], chord[0]]) / chord_length
        candidate_list = []

        # Try both directions.
        for sign in [1, -1]:
            lower, upper = 0, max_offset_pixels  # Reset bounds for this sign.
            best_candidate_dir = None

            while upper - lower > tol:
                mid_offset = (lower + upper) / 2.0
                mid = (p0 + p_end) / 2 + sign * perp * mid_offset
                candidate_segment = [segment[0], tuple(mid), segment[-1]]
                candidate_curve = self.bezier_curve(candidate_segment, num_points=100)
                collision = self.check_collision(candidate_curve)

                if not collision:
                    best_candidate_dir = candidate_segment
                    upper = mid_offset  # Try a smaller offset.
                else:
                    lower = mid_offset  # Increase offset.

            if best_candidate_dir is not None:
                candidate_list.append(best_candidate_dir)

        if candidate_list:
            # Choose the candidate with the smallest offset from the chord's midpoint.
            def candidate_offset(candidate):
                mid = np.array(candidate[1])
                return np.linalg.norm(mid - (p0 + p_end) / 2)

            best_candidate = min(candidate_list, key=candidate_offset)

            return best_candidate
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


def deflate_inflection_points(points, distance_threshold=2):
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


def apply_and_inflate_all_static_obstacles(grid, static_obs_array, safe_distance):
    """
    Applies both static and dynamic obstacles (with inflation) onto the grid,
    ensuring that inflated obstacles do not go out of bounds.
    """
    # --- Apply static obstacles ---
    for coord in static_obs_array:
        x, y = coord
        if 0 <= x < grid.shape[1] and 0 <= y < grid.shape[0]:
            grid[y, x] = 1000000
    # Inflate static obstacles using dilation.
    binary_static = (grid > 1).astype(np.uint8)
    kernel_size = int(2 * safe_distance)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
    inflated_static = cv2.dilate(binary_static, kernel, iterations=1)
    grid[inflated_static == 1] = 101
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


def filter_control_points(segments, grid, threshold=1):
    """
    For each segment (an array of control points in pixel coordinates),
    remove any point whose corresponding cell in 'grid' has a value >= threshold.
    Only segments with at least 2 remaining points are kept.
    """
    filtered_segments = []
    for seg in segments:
        filtered_seg = []
        for pt in seg:
            x = int(round(pt[0]))
            y = int(round(pt[1]))
            if 0 <= x < grid.shape[1] and 0 <= y < grid.shape[0]:
                if grid[y, x] < threshold:
                    filtered_seg.append(pt)
        if len(filtered_seg) >= 2:
            filtered_segments.append(np.array(filtered_seg))
    return filtered_segments


def build_bezier_curves_proto(final_segments, options):
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
    bezier_curves_msg.options.CopyFrom(options)

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


def filter_path_until_first_non_heat(path, grid, threshold=100):
    """
    Filters out the initial points in the path that are 'heated' until the first point
    is found where the grid value is below the threshold. The remaining points in the path
    are returned unmodified.

    Args:
        path (list or np.ndarray): A list (or array) of (x, y) points representing the path.
        grid (np.ndarray): 2D array representing the grid with heat values.
        threshold (float): The heat threshold; cells with values >= threshold are considered hot.

    Returns:
        list: The filtered path starting from the first non-heated point.
              If all points are heated or the path is empty, returns an empty list.
    """
    for i, pt in enumerate(path):
        x = int(round(pt[0]))
        y = int(round(pt[1]))
        # Check if the point is within grid bounds
        if 0 <= x < grid.shape[1] and 0 <= y < grid.shape[0]:
            if grid[y, x] < threshold:
                # Found the first non-heated point: return the remainder of the path.
                return path[i:]
    # If no non-heated point is found, return an empty list.
    return []


# ----------- CONSTANTS (DO NOT CHANGE UNLESS KNOWN) -------------
fieldHeightMeters = 8.05
fieldWidthMeters = 17.55
grid_width = 690
grid_height = 316
ROBOT_SIZE_LENGTH_INCHES = 36
ROBOT_SIZE_WIDTH_INCHES = 36
DEFAULT_SAFE_DISTANCE_INCHES = 0
# ----------- CONSTANTS (DO NOT CHANGE UNLESS KNOWN) -------------


# ----------- MAIN CODE (DO NOT EDIT) -------------
MAX_ROBOT_SIZE_DIAGONAL_INCHES = math.sqrt(
    ROBOT_SIZE_LENGTH_INCHES**2 + ROBOT_SIZE_WIDTH_INCHES**2
)

print("Robot Diagonal Distance (in): ", MAX_ROBOT_SIZE_DIAGONAL_INCHES)
CENTER_ROBOT_SIZE = MAX_ROBOT_SIZE_DIAGONAL_INCHES / 2
print("Robot Center Size (in): ", CENTER_ROBOT_SIZE)
PIXELS_PER_METER_X = grid_width / fieldWidthMeters
PIXELS_PER_METER_Y = grid_height / fieldHeightMeters

low_hanging_red_far_active = False
low_hanging_red_mid_active = False
low_hanging_red_close_active = False
low_hanging_blue_far_active = False
low_hanging_blue_mid_active = False
low_hanging_blue_close_active = False

# ----- SET THIS VALUE TO FALSE WHEN DEPLOYING ON ORIN ----
isRelativePath = False

print("Loading pre-set static obstacles...")
pathPrefix = "" if isRelativePath else "pathplanning/nmc/"
static_obs_array = get_static_obstacles(pathPrefix + "static_obstacles_inch.json")
static_hang_obs_red_far = get_static_obstacles(
    pathPrefix + "static_obstacles_inch_red_far.json"
)
static_hang_obs_red_mid = get_static_obstacles(
    pathPrefix + "static_obstacles_inch_red_mid.json"
)
static_hang_obs_red_close = get_static_obstacles(
    pathPrefix + "static_obstacles_inch_red_close.json"
)
static_hang_obs_blue_far = get_static_obstacles(
    pathPrefix + "static_obstacles_inch_blue_far.json"
)
static_hang_obs_blue_mid = get_static_obstacles(
    pathPrefix + "static_obstacles_inch_blue_mid.json"
)
static_hang_obs_blue_close = get_static_obstacles(
    pathPrefix + "static_obstacles_inch_blue_close.json"
)
print("Finished loading pre-set static obstacles...")


def pathplan(request):
    base_grid = np.ones((grid_height, grid_width), dtype=float)
    start = (request.start.x, request.start.y)
    goal = (request.end.x, request.end.y)
    print(f"{start=} {goal=}")

    SAFE_DISTANCE_INCHES = (
        max(DEFAULT_SAFE_DISTANCE_INCHES, request.safeDistanceInches)
        if request.HasField("safeDistanceInches")
        else DEFAULT_SAFE_DISTANCE_INCHES
    )
    print("Safe Distance (in): ", SAFE_DISTANCE_INCHES)
    TOTAL_SAFE_DISTANCE = int(CENTER_ROBOT_SIZE + SAFE_DISTANCE_INCHES)
    print("Total Safe Distance (in): ", TOTAL_SAFE_DISTANCE)
    modified_static_obs = static_obs_array.copy()
    if low_hanging_red_far_active:
        modified_static_obs.extend(static_hang_obs_red_far)
    if low_hanging_red_mid_active:
        modified_static_obs.extend(static_hang_obs_red_mid)
    if low_hanging_red_close_active:
        modified_static_obs.extend(static_hang_obs_red_close)
    if low_hanging_blue_far_active:
        modified_static_obs.extend(static_hang_obs_blue_far)
    if low_hanging_blue_mid_active:
        modified_static_obs.extend(static_hang_obs_blue_mid)
    if low_hanging_blue_close_active:
        modified_static_obs.extend(static_hang_obs_blue_close)

    static_grid = apply_and_inflate_all_static_obstacles(
        base_grid, modified_static_obs, TOTAL_SAFE_DISTANCE
    )

    pathfinder = FastMarchingPathfinder(static_grid)
    START = (int(start[0] * PIXELS_PER_METER_X), int(start[1] * PIXELS_PER_METER_Y))
    GOAL = (int(goal[0] * PIXELS_PER_METER_X), int(goal[1] * PIXELS_PER_METER_Y))
    time_map = pathfinder.compute_time_map(GOAL)
    path = [START]
    current = START
    max_steps = 10000
    print("Generating path...")
    t = time.time()
    for _ in range(max_steps):
        next_cell = pathfinder.next_step(current, time_map)
        if next_cell == current:
            break  # No progress: local minimum reached.
        path.append(next_cell)
        current = next_cell
        if current == goal:
            break
    print(f"Finished generating path in {(time.time() - t) * 1000:.3f} ms.")
    t = time.time()
    # Filter the initial segment that is "hot"
    path = filter_path_until_first_non_heat(path, static_grid)
    print(f"Finished filtering path in {(time.time() - t) * 1000:.3f} ms.")

    inflection_points = find_inflection_points(path)
    if SAFE_DISTANCE_INCHES >= 10:
        smoothed_control_points = deflate_inflection_points(
            inflection_points, distance_threshold=4
        )
    else:
        smoothed_control_points = deflate_inflection_points(inflection_points)

    print("Finding safe bezier paths...")
    t = time.time()
    safe_bezier_segments = pathfinder.generate_safe_bezier_paths(
        smoothed_control_points
    )
    print(f"Finished finding safe bezier paths in {(time.time() - t) * 1000:.3f} ms.")
    safe_bezier_segments_poses = [
        segment / np.array([PIXELS_PER_METER_X, PIXELS_PER_METER_Y])
        for segment in safe_bezier_segments
    ]
    response = build_bezier_curves_proto(safe_bezier_segments_poses, request.options)
    return response


class VisionCoprocessorServicer(XTableGRPC.VisionCoprocessorServicer):
    def RequestBezierPathWithOptions(self, request, context):
        return pathplan(request)


def serve() -> None:
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    servicer = VisionCoprocessorServicer()
    XTableGRPC.add_VisionCoprocessorServicer_to_server(servicer, server)

    server.add_insecure_port("[::]:9281")  # Listen on all interfaces
    server.start()
    print("RPC Server is running on port 9281...")

    try:
        server.wait_for_termination()  # This BLOCKS until the program is shutdown from a KILL signal etc.
    except KeyboardInterrupt:
        print("Shutting down RPC server.")


# ----------- MAIN CODE (DO NOT EDIT) -------------


if __name__ == "__main__":
    serve()
