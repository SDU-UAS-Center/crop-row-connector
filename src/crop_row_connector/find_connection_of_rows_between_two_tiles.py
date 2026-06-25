"""Find connection of rows between two tiles."""

from typing import Any

import matplotlib.pyplot as plt
import numpy as np

import crop_row_connector.Hungarian_algorithm as HA


class Tile:
    """Hold tile information."""

    def __init__(self, tile_number: int, position: list[float], angle: float, rows: np.ndarray) -> None:
        self.tile_number = tile_number
        self.position = position
        self.angle = angle

        self.rows = rows
        self.unused_rows = rows[:, 0].tolist()  # Row numbers


class FindConnectionOfRowsBetweenTwoTiles:
    """Find connection of rows between two tiles."""

    def __init__(self) -> None:
        self.Hun_alg = HA.HungarianAlgorithm()
        self.distance_tolerance: float
        self.removed_connections = 0
        self.removed_padded_connections = 0

    def calculate_connections_between_2_tiles(self, tile_1: Tile, tile_2: Tile) -> np.ndarray:
        """Calculate the connections between two tiles based on the edges of the tiles."""
        cost_mat_hung, cost_mat_dist = self.cost_matrix_global(tile_1.rows, tile_2.rows)

        connection_matrix = self.Hun_alg.hungarian_algorithm(cost_mat_hung)
        connection_matrix = self.remove_padded_rows_cols(
            tile_1.rows,
            tile_2.rows,
            connection_matrix,
            cost_mat_dist,
        )
        self.keep_track_of_unused_rows_in_tiles(tile_1, tile_2, connection_matrix)

        return connection_matrix

    def cost_matrix_global(self, tile_1_rows: np.ndarray, tile_2_rows: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
        largest_length = np.max([tile_1_rows.shape[0], tile_2_rows.shape[0]])
        cost_mat_hung = np.zeros((largest_length, largest_length))
        cost_mat_dist = np.zeros((largest_length, largest_length))
        for i in range(0, tile_1_rows.shape[0]):
            for j in range(0, tile_2_rows.shape[0]):
                dist = self.distance_between_rows(tile_1_rows[i], tile_2_rows[j])
                cost_mat_dist[i, j] = dist
                if dist < self.distance_tolerance:
                    cost_mat_hung[i, j] = dist
                else:
                    cost_mat_hung[i, j] = self.distance_tolerance

        return cost_mat_hung, cost_mat_dist

    def distance_between_rows(self, row_1: np.ndarray, row_2: np.ndarray) -> float:
        """Calculate the distance between two rows as the difference between the point in one row and the two other points in the other row."""
        row_1_far, row_2_far, row_1_close, row_2_close = self.determine_points_relations(row_1, row_2)

        dist_vec1 = self.distance_between_point_and_line(row_2_close, row_1_close, row_1_far)
        dist_vec2 = self.distance_between_point_and_line(row_1_close, row_2_close, row_2_far)
        avg_dist = float(np.linalg.norm(dist_vec1) + np.linalg.norm(dist_vec2)) / 2

        if row_1[0] == 9 and row_2[0] == 0 and False:
            plt.scatter(row_1_close[0], row_1_close[1], color="blue")
            plt.scatter(row_1_far[0], row_1_far[1], color="red")
            plt.scatter(row_2_close[0], row_2_close[1], color="green")
            plt.scatter(row_2_far[0], row_2_far[1], color="yellow")
            plt.plot([row_1_close[0], row_1_far[0]], [row_1_close[1], row_1_far[1]], color="red")
            plt.plot([row_2_close[0], row_2_far[0]], [row_2_close[1], row_2_far[1]], color="green")
            plt.plot(
                [row_2_close[0], row_2_close[0] - dist_vec1[0]],
                [row_2_close[1], row_2_close[1] - dist_vec1[1]],
                color="black",
            )
            plt.plot(
                [row_1_close[0], row_1_close[0] - dist_vec2[0]],
                [row_1_close[1], row_1_close[1] - dist_vec2[1]],
                color="black",
            )
            plt.axis("equal")
            plt.show()

        return avg_dist

    def determine_points_relations(self, row_1: np.ndarray, row_2: np.ndarray) -> tuple[Any, Any, Any, Any]:
        largest_distance = [0, 0, 0]
        row_1_re = row_1[1:].reshape(-1, 2)
        row_2_re = row_2[1:].reshape(-1, 2)

        # minus 1 is to not use the middle point of the lines
        for i in range(0, row_1_re.shape[0] - 1):
            for j in range(0, row_2_re.shape[0] - 1):
                distance = np.sqrt((row_1_re[i][0] - row_2_re[j][0]) ** 2 + (row_1_re[i][1] - row_2_re[j][1]) ** 2)
                if distance > largest_distance[0]:
                    largest_distance = [distance, i, j]

        row_1_far = row_1_re[largest_distance[1]]
        row_2_far = row_2_re[largest_distance[2]]

        if largest_distance[1] == 0:
            row_1_close = row_1_re[1]
        else:
            row_1_close = row_1_re[0]

        if largest_distance[2] == 0:
            row_2_close = row_2_re[1]
        else:
            row_2_close = row_2_re[0]
        return row_1_far, row_2_far, row_1_close, row_2_close

    def distance_between_point_and_line(
        self, point: np.ndarray, line_point_close: np.ndarray, line_point_far: np.ndarray
    ) -> np.ndarray:
        """Calculate the distance between a point and a line."""
        vec_line = line_point_far - line_point_close
        vec_point_close_point = point - line_point_close
        projection = (np.dot(vec_point_close_point, vec_line) / np.dot(vec_line, vec_line)) * vec_line
        dist_vec = vec_point_close_point - projection

        return dist_vec

    def remove_padded_rows_cols(
        self,
        tile_1_rows: np.ndarray,
        tile_2_rows: np.ndarray,
        connection_matrix: np.ndarray,
        cost_mat: np.ndarray,
    ) -> np.ndarray:
        """Remove the padded rows and columns from the connection matrix, as well as the rows that are too far apart."""
        for i in range(0, connection_matrix.shape[0]):
            if connection_matrix[i, 0] >= tile_1_rows.shape[0]:
                connection_matrix[i, 0] = -1
                self.removed_padded_connections += 1
            elif connection_matrix[i, 1] >= tile_2_rows.shape[0]:
                connection_matrix[i, 1] = -1
                self.removed_padded_connections += 1
            elif cost_mat[connection_matrix[i, 0], connection_matrix[i, 1]] > self.distance_tolerance:
                connection_matrix[i, 0] = -1
                connection_matrix[i, 1] = -1
                self.removed_connections += 1

        connection_matrix = connection_matrix[connection_matrix[:, 0] != -1]
        connection_matrix = connection_matrix[connection_matrix[:, 1] != -1]
        connection_matrix = connection_matrix[connection_matrix[:, 0].argsort()]
        return connection_matrix

    def keep_track_of_unused_rows_in_tiles(self, tile_1: Tile, tile_2: Tile, connection_matrix: np.ndarray) -> None:
        """Remove rows when they have been used in a connection."""
        for i in range(0, connection_matrix.shape[0]):
            if connection_matrix[i, 0] in tile_1.unused_rows:
                tile_1.unused_rows.remove(connection_matrix[i, 0])
            if connection_matrix[i, 1] in tile_2.unused_rows:
                tile_2.unused_rows.remove(connection_matrix[i, 1])
