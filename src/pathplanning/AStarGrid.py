import heapq
from typing import Any, Optional

import cv2
import numpy as np

import math


class Cell:
    def __init__(self):
        self.parent_i = 0  # Parent cell's row index
        self.parent_j = 0  # Parent cell's column index
        self.f = float("inf")  # Total cost of the cell (g + h)
        self.g = float("inf")  # Cost from start to this cell
        self.h = 0  # Heuristic cost from this cell to destination


class AStarPathfinder:
    def __init__(
        self,
        grid: np.ndarray,
        obstacleWidth: float,
        obstacleHeight: float,
        gridSizeCol: int,
        gridSizeRow: int,
        mapResolution: float,
    ):
        self.original_grid = grid
        self.obstacle_radius = math.ceil(
            np.linalg.norm((obstacleWidth, obstacleHeight))
        )
        self.obstacle_radius_small = math.ceil(
            np.linalg.norm(
                (obstacleWidth / mapResolution, obstacleHeight / mapResolution)
            )
        )
        self.grid = self.inflate_obstacles(grid, self.obstacle_radius)
        self.grid = cv2.resize(self.grid, (gridSizeCol, gridSizeRow))
        # cv2.imshow("grid",self.grid*255)
        # now convert back to boolean
        self.grid = self.grid >= 1
        self.ROW_SIZE = gridSizeRow
        self.COL_SIZE = gridSizeCol

    def inflate_obstacles(self, grid: Any, radius: int) -> Any:
        # Create a circular kernel
        kernel_size = int(2 * radius)  # small safety offset
        kernel = cv2.getStructuringElement(
            cv2.MORPH_ELLIPSE, (kernel_size, kernel_size)
        )
        # Dilate the grid to inflate obstacles
        inflated_grid = cv2.dilate(grid.astype(dtype=np.uint8), kernel, iterations=1)
        return inflated_grid

    @staticmethod
    def is_valid(col: int, row: int, ROW_SIZE: int, COL_SIZE: int) -> bool:
        return 0 <= row < ROW_SIZE and 0 <= col < COL_SIZE

    def is_unblocked(self, col: int, row: int, grid: Any) -> bool:
        return not grid[row, col]

    @staticmethod
    def is_destination(col: int, row: int, dest: list[int]) -> bool:
        return col == dest[0] and row == dest[1]

    @staticmethod
    def calculate_h_value(col: int, row: int, dest: list[int]) -> float:
        return ((col - dest[0]) ** 2 + (row - dest[1]) ** 2) ** 0.5

    @staticmethod
    def trace_path(
        cell_details: list[list[Any]], dest: tuple[int, int]
    ) -> list[tuple[int, int]]:
        path = []
        row, col = dest
        while not (
            cell_details[row][col].parent_i == row
            and cell_details[row][col].parent_j == col
        ):
            path.append((row, col))
            temp_row = cell_details[row][col].parent_i
            temp_col = cell_details[row][col].parent_j
            row, col = temp_row, temp_col

        path.append((row, col))
        path.reverse()
        return path

    def a_star_search(
        self, src: list[int], dest: list[int], extraObstacles: np.ndarray = None
    ) -> Optional[list[tuple[int, int]]]:
        grid = self.grid
        print(self.grid.shape)
        if extraObstacles is not None:
            extraObstacles = (
                self.inflate_obstacles(extraObstacles, self.obstacle_radius_small) >= 1
            )
            grid = np.bitwise_or(grid, extraObstacles)

        print(f"{self.ROW_SIZE=} {self.COL_SIZE=}")
        print(f"{src=} {dest=}")
        if not self.is_valid(
            src[0], src[1], self.ROW_SIZE, self.COL_SIZE
        ) or not self.is_valid(dest[0], dest[1], self.ROW_SIZE, self.COL_SIZE):
            print(f"Source {src} or destination {dest} is invalid")
            return None

        if not self.is_unblocked(src[0], src[1], grid) or not self.is_unblocked(
            dest[0], dest[1], grid
        ):
            print("Source or the destination is blocked")
            return None

        if self.is_destination(src[0], src[1], dest):
            print("We are already at the destination")
            return np.array([src])

        closed_list = [
            [False for _ in range(self.ROW_SIZE)] for _ in range(self.COL_SIZE)
        ]
        cell_details = [
            [Cell() for _ in range(self.ROW_SIZE)] for _ in range(self.COL_SIZE)
        ]

        i, j = src
        cell_details[i][j].f = 0
        cell_details[i][j].g = 0
        cell_details[i][j].h = 0
        cell_details[i][j].parent_i = i
        cell_details[i][j].parent_j = j

        open_list = []
        heapq.heappush(open_list, (0.0, i, j))
        found_dest = False

        directions = [
            (0, 1),
            (0, -1),
            (1, 0),
            (-1, 0),
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        ]

        while open_list:
            p = heapq.heappop(open_list)
            i, j = p[1], p[2]
            closed_list[i][j] = True

            for dir in directions:
                new_i, new_j = i + dir[0], j + dir[1]

                if (
                    self.is_valid(new_i, new_j, self.ROW_SIZE, self.COL_SIZE)
                    and self.is_unblocked(new_i, new_j, grid)
                    and not closed_list[new_i][new_j]
                ):
                    if self.is_destination(new_i, new_j, dest):
                        cell_details[new_i][new_j].parent_i = i
                        cell_details[new_i][new_j].parent_j = j
                        print("The destination cell is found")
                        found_dest = True
                        return self.trace_path(cell_details, dest)

                    g_new = cell_details[i][j].g + 1.0
                    h_new = self.calculate_h_value(new_i, new_j, dest)
                    f_new = g_new + h_new

                    if (
                        cell_details[new_i][new_j].f == float("inf")
                        or cell_details[new_i][new_j].f > f_new
                    ):
                        heapq.heappush(open_list, (f_new, new_i, new_j))
                        cell_details[new_i][new_j].f = f_new
                        cell_details[new_i][new_j].g = g_new
                        cell_details[new_i][new_j].h = h_new
                        cell_details[new_i][new_j].parent_i = i
                        cell_details[new_i][new_j].parent_j = j

        if not found_dest:
            print("Failed to find the destination cell")
            return None
