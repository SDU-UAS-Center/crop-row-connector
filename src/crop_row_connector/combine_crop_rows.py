"""Combine crop rows from different tiles into one line."""

import math
import os
from argparse import Namespace
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
import shapefile
from tqdm import tqdm

import crop_row_connector._native as mpro
from crop_row_connector.combine_crop_rows_from_connections import CombineCropRowsFromConnections
from crop_row_connector.find_connection_of_rows_between_two_tiles import FindConnectionOfRowsBetweenTwoTiles, Tile


class CombineCropRows:
    """Combine crop rows from different tiles into one line."""

    def __init__(self) -> None:
        self.angle_tolerance: float
        self.vegetation_threshold = None
        self.min_unhealthy_vegetation_length = None
        self.max_segment_length = None

        # Output paths, if None, the respective output will not be saved
        self.output_path_connected_crop_rows: Path
        self.output_path_vegetation_points = None
        self.output_path_healthy_vegetation_segments = None
        self.output_path_unhealthy_vegetation_segments = None

        self.max_workers = os.cpu_count()

        self.ccbt = FindConnectionOfRowsBetweenTwoTiles()
        self.ccrc = CombineCropRowsFromConnections()

    def ensure_parent_directory_exist(self, path: Path) -> None:
        """
        Ensure the parent directory of `path` exists.

        Notes
        -----
        - Only creates directories if they do not already exist.

        Parameters
        ----------
        path : Path
            The path for which to ensure the parent directory exists.
        """
        path.parent.mkdir(parents=True, exist_ok=True)

    def load_csv(self, path: str) -> np.ndarray:
        """
        Load a CSV file containing row information into a NumPy array.

        Notes
        -----
        - Each row corresponds to a crop row.
        - Columns contain:
            [tile_number, x_position, y_position, angle, row, x_start, y_start, x_end, y_end]

        Parameters
        ----------
        path : str
            The file path to the CSV file containing row information.

        Returns
        -------
        NDArray[np.float64]
            2D array where each row corresponds to a crop row.
        """
        return pd.read_csv(path).to_numpy(dtype=np.float64)

    def seperate_row_information_to_tile(self, row_information: np.ndarray) -> dict[int, Tile]:
        """
        Split row information into tile objects keyed by tile number.

        Parameters
        ----------
        row_information : NDArray[np.float64]
            A NumPy array containing row information for all tiles. Each row corresponds to a crop row and contains the following columns:
            [tile_number, x_position, y_position, angle, row, x_start, y_start, x_end, y_end]

        Returns
        -------
        dict[int, tile]
            Dictionary mapping each tile number to a tile object.
        """
        tile_numbers = np.unique(row_information[:, 0]).astype(int)
        print("Tile numbers: ", tile_numbers)

        tiles = {}

        for tile_number in tile_numbers:
            rows_in_tile = row_information[row_information[:, 0] == tile_number]
            tile_position = rows_in_tile[0, 1:3].astype(int)
            row_angle = rows_in_tile[0, 3]
            rows = rows_in_tile[:, 4:]
            tile_load = Tile(tile_number, tile_position, row_angle, rows)
            tiles.update({tile_number: tile_load})

        return tiles

    def create_tile_grid(self, row_information: np.ndarray, tiles: dict[int, Tile]) -> np.ndarray:
        """
        Create a 2D grid of tile numbers in their respective positions, with -1 for empty cells.

        Notes
        -----
        - X indexes columns, Y indexes rows (grid[y, x])
        - The grid is padded by 1 row and 1 column to simplify neighbor connections.

        Parameters
        ----------
        row_information : np.ndarray
            2D array with row information including tile positions.
        tiles : dict[int, tile]
            Dictionary mapping tile numbers to tile objects.

        Returns
        -------
        np.ndarray
            2D array where each cell contains a tile number if present, otherwise -1.
        """
        tile_grid_size = np.amax(row_information[:, 1:3], axis=0).astype(int)

        grid = np.full((tile_grid_size[0] + 2, tile_grid_size[1] + 2), -1, dtype=np.int32)

        for tile in tiles.values():
            grid[tile.position[0], tile.position[1]] = tile.tile_number

        return grid

    def connect_rows_in_tiles(self, grid: np.ndarray, tiles: dict[int, Tile]) -> None:
        """
        Connect crop rows across neighboring tiles in the grid.

        For each tile in the grid:
        - Connect to its right neighbor (if any)
        - Connect to its bottom neighbor (if any)

        After all connections are made:
        - Add any uncombined rows to the connected crop rows

        Parameters
        ----------
        grid : np.ndarray[int32]
            2D array representing the tile grid. Each entry is a tile number, or -1 for empty cells.
        tiles : dict[int, tile]
            Dictionary mapping tile numbers to tile objects.
        """
        # Find all positions in the grid that contain a tile
        ys, xs = np.where(grid != -1)  #
        for y, x in tqdm(
            zip(ys, xs, strict=False),
            total=len(ys),
            desc="Connecting rows in tiles",
            unit="tiles",
        ):
            tile_current = tiles[grid[y, x]]

            # Connect tile to the right
            tile_right_num = grid[y, x + 1]
            if tile_right_num != -1:
                self.connect_2_tiles(tile_current, tiles[tile_right_num])

            # connect tile below
            tile_below_num = grid[y + 1, x]
            if tile_below_num != -1:
                self.connect_2_tiles(tile_current, tiles[tile_below_num])

        print("removed connections: ", self.ccbt.removed_connections)
        print("removed padded connections: ", self.ccbt.removed_padded_connections)
        print("full connections", self.ccrc.connecting_full)
        print("connections", self.ccrc.connections)

        # Compute which crop row has the most connections
        # connected_crop_rows[:, 0] contains the row IDs
        counts = np.bincount(self.ccrc.connected_crop_rows[:, 0].astype(int))
        max_row_id = np.argmax(counts)
        max_connections = counts[max_row_id]

        print(f"Crop row with most connections: {max_row_id} with {max_connections} connections")

        # add the uncombined rows to the connected crop rows
        self.ccrc.add_unused_rows(tiles)

    def connect_2_tiles(self, tile_1: Tile, tile_2: Tile) -> None:
        """
        Connect two tiles by linking crop rows if their angles are within the allowed tolerance.

        Parameters
        ----------
        tile_1 : tile
            The first tile object to connect.
        tile_2 : tile
            The second tile object to connect.
        """
        # Check if the angle of the two tiles is close enough
        if math.isclose(tile_1.angle, tile_2.angle, abs_tol=self.angle_tolerance):
            connections = self.ccbt.calculate_connections_between_2_tiles(tile_1, tile_2)
            self.ccrc.connect_crop_rows_of_2_tiles(tile_1.tile_number, tile_2.tile_number, connections)

    def connected_crop_rows_to_csv(self, connected_crop_rows: np.ndarray) -> None:
        """
        Write the connected crop rows to a csv file.

        Parameters
        ----------
        connected_crop_rows : np.ndarray
            2D array containing connected crop row information.
        """
        # Write the connected crop rows to a csv file
        DF_connected_crop_rows = pd.DataFrame(
            connected_crop_rows,
            columns=[
                "row_index",
                "tile",
                "row",
                "con_1_tile",
                "con_1_row",
                "con_2_tile",
                "con_2_row",
                "con_3_tile",
                "con_3_row",
                "con_4_tile",
                "con_4_row",
                "dubli_error",
            ],
        )
        self.ensure_parent_directory_exist(self.output_path_connected_crop_rows)
        DF_connected_crop_rows.to_csv(self.output_path_connected_crop_rows, index=False)

    def merge_all_points_in_all_crop_rows_remove(
        self,
        connected_crop_rows: np.ndarray,
        path_points_in_rows: str,
        row_information: np.ndarray,
        tiles: dict[int, Tile],
    ) -> pd.DataFrame:
        """
        Merge all points from connected crop rows into a single DataFrame,
        removing overlapping points based on a distance tolerance.

        Parameters
        ----------
        connected_crop_rows : np.ndarray
            2D array containing connected crop row information.
        path_points_in_rows : str
            Path to CSV containing raw vegetation points per row.
        row_information : np.ndarray
            Original row information array.
        tiles : dict[int, tile]
            Dictionary mapping tile numbers to tile objects.

        Returns
        -------
        pd.DataFrame
            Merged and sorted crop rows including vegetation and duplicate information.
        """
        DF_vegetation_rows = pd.read_csv(path_points_in_rows)

        tolerance = self.ccbt.distance_tolerance / 10

        crop_rows = mpro.merge_points_removing_overlap(
            connected_crop_rows.astype(np.float64),
            DF_vegetation_rows.to_numpy(),
            row_information,
            tolerance,
            self.max_workers,
        )

        DF_crop_rows = pd.DataFrame(crop_rows, columns=DF_vegetation_rows.columns)
        DF_crop_rows["vegetation"] = DF_crop_rows["vegetation"].astype(int)

        DF_connected_crop_rows = pd.DataFrame(connected_crop_rows[:, :3], columns=["crop_row", "tile", "row"])

        DF_connected_crop_rows.insert(1, "duplicate", connected_crop_rows[:, -1])

        DF_crop_rows = pd.merge(
            DF_connected_crop_rows,
            DF_crop_rows,
            left_on=["tile", "row"],
            right_on=["tile", "row"],
            how="left",
        )

        DF_crop_rows_new = pd.DataFrame(columns=DF_crop_rows.columns)
        rows = []
        # sort the crop rows by coordinates
        for _, subset in DF_crop_rows.groupby("crop_row", sort=False):
            tile_number = subset["tile"].iat[0]
            angle = tiles[tile_number].angle

            if angle < math.pi / 4 or angle > 3 * math.pi / 4:
                crop_row = subset.sort_values(by=["y", "x"])
            else:
                crop_row = subset.sort_values(by=["x", "y"])

            rows.append(crop_row)

        DF_crop_rows_new = pd.concat(rows, ignore_index=True)

        DF_crop_rows_new = DF_crop_rows_new.drop(columns=["tile", "row"]).rename(columns={"crop_row": "row"})[
            ["row", "x", "y", "vegetation", "duplicate"]
        ]

        if self.output_path_vegetation_points is not None:
            path = self.output_path_vegetation_points
            self.ensure_parent_directory_exist(Path(path))
            DF_crop_rows_new.to_csv(path, index=False)

        return DF_crop_rows_new

    def add_segment(self, target: list[list[np.ndarray]], start_idx: int, end_idx: int, coords: np.ndarray) -> None:
        if self.max_segment_length is None or self.max_segment_length <= 0:
            target.append([coords[start_idx].tolist(), coords[end_idx].tolist()])
            return

        seg_start = start_idx
        added = False

        for j in range(start_idx + 1, end_idx + 1):
            p_seg_start = coords[seg_start]
            p_curr = coords[j]
            dist_from_start = math.hypot(p_curr[0] - p_seg_start[0], p_curr[1] - p_seg_start[1])

            if dist_from_start > self.max_segment_length:
                # Current point exceeds max_segment_length, end segment at previous point
                target.append([coords[seg_start].tolist(), coords[j - 1].tolist()])
                seg_start = j - 1
                added = True

        if seg_start < end_idx:
            target.append([coords[seg_start].tolist(), coords[end_idx].tolist()])
            added = True

        if not added:
            target.append([coords[start_idx].tolist(), coords[end_idx].tolist()])

    def run_distance(self, s: int, e: int, coords: np.ndarray) -> float:
        dx = coords[s][0] - coords[e][0]
        dy = coords[s][1] - coords[e][1]
        return math.hypot(dx, dy)

    def separate_healthy_and_unhealthy_vegetation_segments(self, DF_crop_rows: pd.DataFrame) -> list[dict[str, Any]]:
        """
        Define healthy and unhealthy vegetation segments and optionally write them to shapefiles.

        Notes
        -----
        - Uses self.vegetation_threshold to separate healthy from unhealthy vegetation.
        - Each segment is represented as a line between two points.
        - Returns segments so they can be reused for further analysis (e.g. length calculation).
        - X indexes columns, Y indexes rows (DF_crop_rows['x'], DF_crop_rows['y']).

        Parameters
        ----------
        DF_crop_rows : pd.DataFrame
            DataFrame containing at least ['row', 'x', 'y', 'vegetation'].

        Returns
        -------
        list[dict]
            List of segment dictionaries:
            {
                "row_id": int,
                "healthy": list[[[x1, y1], [x2, y2]]],
                "unhealthy": list[[[x1, y1], [x2, y2]]]
            }
        """
        writer_healthy = None
        writer_unhealthy = None

        if self.output_path_healthy_vegetation_segments is not None:
            writer_healthy = shapefile.Writer(self.output_path_healthy_vegetation_segments)
            writer_healthy.field("Crop_row", "N")

        if self.output_path_unhealthy_vegetation_segments is not None:
            writer_unhealthy = shapefile.Writer(self.output_path_unhealthy_vegetation_segments)
            writer_unhealthy.field("Crop_row", "N")

        segments = []

        for crop_row_id, crop_row in DF_crop_rows.groupby("row", sort=False):
            coords = crop_row[["x", "y"]].to_numpy(dtype=np.float64)
            vegetation = crop_row["vegetation"].to_numpy()

            n = len(coords)
            if n < 2:
                continue

            healthy_lines: list[list[np.ndarray]] = []
            unhealthy_lines: list[list[np.ndarray]] = []

            # Build runs of contiguous healthy/unhealthy points
            healthy_mask = vegetation >= self.vegetation_threshold
            runs: list[tuple[bool, int, int]] = []  # (is_healthy, start, end)
            run_start = 0
            run_state = bool(healthy_mask[0])
            for i in range(1, n):
                if bool(healthy_mask[i]) != run_state:
                    runs.append((run_state, run_start, i - 1))
                    run_start = i
                    run_state = bool(healthy_mask[i])
            runs.append((run_state, run_start, n - 1))

            # If no healthy runs exist, everything is unhealthy
            if not any(is_healthy for is_healthy, _, _ in runs):
                self.add_segment(unhealthy_lines, 0, n - 1, coords)
            else:
                # Merge short unhealthy runs into neighboring healthy runs
                merged_runs: list[tuple[bool, int, int]] = []
                i = 0
                while i < len(runs):
                    is_healthy, s, e = runs[i]
                    if not is_healthy:
                        dist = self.run_distance(s, e, coords)
                        if (
                            self.min_unhealthy_vegetation_length is not None
                            and dist < self.min_unhealthy_vegetation_length
                        ):
                            prev_is_healthy = bool(merged_runs and merged_runs[-1][0])
                            next_index = i + 1
                            next_is_healthy = next_index < len(runs) and runs[next_index][0]

                            if prev_is_healthy and next_is_healthy:
                                prev_run = merged_runs.pop()
                                next_run = runs[next_index]
                                merged_runs.append((True, prev_run[1], next_run[2]))
                                i += 2
                                continue
                            if prev_is_healthy:
                                prev_run = merged_runs.pop()
                                merged_runs.append((True, prev_run[1], e))
                                i += 1
                                continue
                            if next_is_healthy:
                                runs[next_index] = (True, s, runs[next_index][2])
                                i += 1
                                continue

                    merged_runs.append((is_healthy, s, e))
                    i += 1

                # Emit final segments (with max-length splitting applied)
                for is_healthy, s, e in merged_runs:
                    if is_healthy:
                        self.add_segment(healthy_lines, s, e, coords)
                    else:
                        self.add_segment(unhealthy_lines, s, e, coords)

            segments.append(
                {
                    "row_id": int(crop_row_id),
                    "healthy": healthy_lines,
                    "unhealthy": unhealthy_lines,
                }
            )

            # Write shapefiles if enabled
            if healthy_lines and writer_healthy is not None:
                writer_healthy.line(healthy_lines)
                writer_healthy.record(int(crop_row_id))

            if unhealthy_lines and writer_unhealthy is not None:
                writer_unhealthy.line(unhealthy_lines)
                writer_unhealthy.record(int(crop_row_id))

        if writer_healthy is not None:
            writer_healthy.close()
        if writer_unhealthy is not None:
            writer_unhealthy.close()

        return segments

    def length_of_segments(self, segments: list[dict[str, Any]]) -> tuple[float, float, float]:
        """
        Calculate total lengths of healthy and unhealthy vegetation segments.

        Notes
        -----
        - Uses segment endpoints instead of point-to-point distances.
        - Each segment is treated as a straight line.

        Parameters
        ----------
        segments : list[dict]
            Output from separate_healthy_and_unhealthy_vegetation_segments.

        Returns
        -------
        tuple[float, float, float]
            (total_length, healthy_length, unhealthy_length)
        """
        total_length = 0.0
        healthy_length = 0.0
        unhealthy_length = 0.0

        for row in segments:
            # Healthy segments
            if len(row["healthy"]) > 0:
                for seg in row["healthy"]:
                    if not (
                        math.isnan(seg[0][0]) or math.isnan(seg[0][1]) or math.isnan(seg[1][0]) or math.isnan(seg[1][1])
                    ):
                        dx = seg[0][0] - seg[1][0]
                        dy = seg[0][1] - seg[1][1]
                        length = math.hypot(dx, dy)

                        healthy_length += length
                        total_length += length

            # Unhealthy segments
            if len(row["unhealthy"]) > 0:
                for seg in row["unhealthy"]:
                    if not (
                        math.isnan(seg[0][0]) or math.isnan(seg[0][1]) or math.isnan(seg[1][0]) or math.isnan(seg[1][1])
                    ):
                        dx = seg[0][0] - seg[1][0]
                        dy = seg[0][1] - seg[1][1]
                        length = math.hypot(dx, dy)

                        unhealthy_length += length
                        total_length += length

        if math.isnan(unhealthy_length):
            print("!!!!!! length is nan")

        print("Total length:", total_length)
        print("Healthy vegetation length:", healthy_length)
        print("Unhealthy vegetation length:", unhealthy_length)

        return total_length, healthy_length, unhealthy_length

    def main(self, path_row_information: str, path_points_in_rows: str) -> None:
        row_information = self.load_csv(path_row_information)

        tiles = self.seperate_row_information_to_tile(row_information)

        grid = self.create_tile_grid(row_information, tiles)

        self.connect_rows_in_tiles(grid, tiles)

        self.ccrc.sort_connected_crop_rows()

        self.ccrc.check_dublicates()

        if self.output_path_connected_crop_rows is not None:
            self.connected_crop_rows_to_csv(self.ccrc.connected_crop_rows)

        DF_crop_rows_new = self.merge_all_points_in_all_crop_rows_remove(
            self.ccrc.connected_crop_rows, path_points_in_rows, row_information, tiles
        )

        if (
            self.output_path_healthy_vegetation_segments is not None
            or self.output_path_unhealthy_vegetation_segments is not None
        ):
            segments = self.separate_healthy_and_unhealthy_vegetation_segments(DF_crop_rows_new)
            self.length_of_segments(segments)

    def save_statistics(self, stat_path: Path, args: Namespace, tiles: list[Tile]) -> None:
        """Save the statistics of the run to a file."""
        print(f'Writing statistics to the folder "{stat_path}"')

        with open(stat_path.joinpath("/output_file.txt"), "w") as f:
            f.write("Input parameters:\n")
            f.write(f" - Segmented Orthomosaic: {args.segmented_orthomosaic}\n")
            f.write(f" - Orthomosaic: {args.orthomosaic}\n")
            f.write(f" - Tile sizes: {args.tile_size}\n")
            f.write(f" - Output tile location: {args.output_tile_location}\n")
            f.write(f" - Generated debug images: {args.generate_debug_images}\n")
            f.write(f" - Tile boundary: {args.tile_boundary}\n")
            f.write(f" - Ecpected crop row distance: {args.expected_crop_row_distance}\n")
            f.write(f" - Date and time of execution: {datetime.now().replace(microsecond=0)}\n")
            f.write("\n\nOutput from run\n")
            f.write(f" - Number of tiles: {len(tiles)}\n")
