import pandas as pd  # type: ignore
import numpy as np  # type: ignore
from numpy.typing import NDArray  # type: ignore
from typing import Any  # type: ignore
import math  # type: ignore
import time  # type: ignore
import os  # type: ignore
from datetime import datetime  # type: ignore
from pathlib import Path  # type: ignore

# from icecream import ic # type: ignore
from tqdm import tqdm  # type: ignore

import crop_row_connector.find_connection_of_rows_between_two_tiles as find_connection_of_rows_between_two_tiles
import crop_row_connector.combine_crop_rows_from_connections as combine_crop_rows_from_connections

import crop_row_connector._native as mpro

import shapefile  # type: ignore

def timeit(func):
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"Time taken by {func.__name__}: {(end_time - start_time):.4f} seconds")
        return result
    return wrapper

class tile:
    def __init__(
        self, tile_number: int, position: list[float], angle: float, rows: NDArray[np.float64]
    ) -> None:
        self.tile_number = tile_number
        self.position = position
        self.angle = angle

        self.rows = rows
        self.unused_rows = rows[:, 0].astype(int).tolist()  # Row numbers


class Combine_crop_rows:
    def __init__(self) -> None:
        self.angle_tolerance = None
        self.vegetation_threshold = None
        self.unhealthy_vegetation_length = None

        # Output paths, if None, the respective output will not be saved
        self.output_path_connected_crop_rows = None
        self.output_path_vegetation_points = None
        self.output_path_healthy_vegetation_segments = None
        self.output_path_unhealthy_vegetation_segments = None
        

        self.max_workers = os.cpu_count()

        self.ccbt = find_connection_of_rows_between_two_tiles.find_connection_of_rows_between_two_tiles()
        self.ccrc = combine_crop_rows_from_connections.combine_crop_rows_from_connections()

    def ensure_parent_directory_exist(self, path: Path) -> None:
        """
        Ensure the parent directory of `path` exists.

        Notes:
        - Only creates directories if they do not already exist.

        Parameters
        ----------
        path : Path
            The path for which to ensure the parent directory exists.
        """

        path.parent.mkdir(parents=True, exist_ok=True)

    def load_csv(self, path: str) -> NDArray[np.float64]:
        """
        Load a CSV file containing row information into a NumPy array.

        Notes:
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

    def seperate_row_information_to_tile(
        self, row_information: NDArray[np.float64]
    ) -> dict[int, tile]:
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
            tile_load = tile(tile_number, tile_position, row_angle, rows)
            tiles.update({tile_number: tile_load})

        return tiles

    def create_tile_grid(
        self, row_information: NDArray[np.float64], tiles: dict[int, tile]
    ) -> NDArray[np.int32]:
        """
        Create a 2D grid of tile numbers in their respective positions, with -1 for empty cells.

        Notes:
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

    def connect_rows_in_tiles(self, grid: NDArray[np.int32], tiles: dict[int, tile]) -> None:
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
        ys, xs = np.where(grid != -1) #
        for y, x in tqdm(
            zip(ys, xs),
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

    def connect_2_tiles(self, tile_1: tile, tile_2: tile) -> None:
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
            connections = self.ccbt.calculate_connections_between_2_tiles(
                tile_1, tile_2
            )
            self.ccrc.connect_crop_rows_of_2_tiles(
                tile_1.tile_number, tile_2.tile_number, connections
            )


    def connected_crop_rows_to_csv(self, connected_crop_rows: NDArray[Any]) -> None:
        """
        Write the connected crop rows to a csv file

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
        path = self.output_path_connected_crop_rows
        self.ensure_parent_directory_exist(Path(path))
        DF_connected_crop_rows.to_csv(path, index=False)

    def merge_all_points_in_all_crop_rows_remove(
        self,
        connected_crop_rows: NDArray[Any],
        path_points_in_rows: str,
        row_information: NDArray[Any],
        tiles: dict[int, tile],
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

        crop_rows = timeit(mpro.merge_points_removing_overlap)(
            connected_crop_rows.astype(np.float64), 
            DF_vegetation_rows.to_numpy(), 
            row_information, 
            tolerance, 
            self.max_workers
        )


        DF_crop_rows = pd.DataFrame(crop_rows, columns=DF_vegetation_rows.columns)
        DF_crop_rows["vegetation"] = DF_crop_rows["vegetation"].astype(int)

        DF_connected_crop_rows = pd.DataFrame(
            connected_crop_rows[:, :3], columns=["crop_row", "tile", "row"]
        )

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
        for crop_row_id, subset in DF_crop_rows.groupby("crop_row"):
            tile_number = subset["tile"].mode()[0]
            angle = tiles[tile_number].angle

            if angle < math.pi / 4 or angle > 3 * math.pi / 4:
                crop_row = subset.sort_values(by=["y", "x"])
            else:
                crop_row = subset.sort_values(by=["x", "y"])

            rows.append(crop_row)

        DF_crop_rows_new = pd.concat(rows, ignore_index=True)

        DF_crop_rows_new = DF_crop_rows_new.drop(columns=["tile", "row"])
        DF_crop_rows_new = DF_crop_rows_new.rename(columns={"crop_row": "row"})
        DF_crop_rows_new = DF_crop_rows_new[["row", "x", "y", "vegetation", "duplicate"]]

        #self.length_of_all_crop_rows(DF_crop_rows.to_numpy())
        if self.output_path_vegetation_points is not None:
            path = self.output_path_vegetation_points
            self.ensure_parent_directory_exist(Path(path))
            DF_crop_rows_new.to_csv(path, index=False)

        return DF_crop_rows_new

    def length_of_all_crop_rows(self, crop_rows: NDArray[Any]) -> float:
        """
        Calculate the length of all crop rows
        """

        total_time = 0.0

        length_low_vegetation = 0.0
        length_high_vegetation = 0.0

        total_field_length = 0.0
        total_length = 0.0
        curr_id = 0
        for i in range(len(crop_rows)-1):
            if crop_rows[i, 0] != curr_id:
                print("Length of crop row ", curr_id, ": ", total_length)
                curr_id = crop_rows[i, 0]
                total_field_length += total_length
                total_length = 0.0
                #assert False

            next_row = crop_rows[i + 1]

            time_start = time.time()
            length = np.linalg.norm(
                np.array([crop_rows[i, 1], crop_rows[i, 2]])
                - np.array([next_row[1], next_row[2]])
            )

            total_time += time.time() - time_start
            if length < self.ccbt.distance_tolerance:
                total_length += length
                if crop_rows[i, 3] < 20: # arbitrary threshold for low vegetation
                    length_low_vegetation += length
                else:
                    length_high_vegetation += length
        total_field_length += total_length
        print("Time to calculate length of all crop rows: ", total_time)
        print("Total length of all crop rows: ", total_field_length)
        print("Healthy vegetation length: ", length_high_vegetation)
        print("Low vegetation length: ", length_low_vegetation)
        return total_length

    def seperate_healthy_and_unhealthy_vegetation_segments(self, DF_crop_rows: pd.DataFrame) -> None:
        """
        Define healthy vegetation based on a threshold
        """

        if self.output_path_healthy_vegetation_segments is not None:
            writer_healthy = shapefile.Writer(self.output_path_healthy_vegetation_segments)
            writer_healthy.field("Crop_row", "N")

        if self.output_path_unhealthy_vegetation_segments is not None:
            writer_unhealthy = shapefile.Writer(self.output_path_unhealthy_vegetation_segments)
            writer_unhealthy.field("Crop_row", "N")

        for crop_row_id in DF_crop_rows["row"].unique():
            crop_row = DF_crop_rows[DF_crop_rows["row"] == crop_row_id]

            start, middle, end = 0, 0, 0
            in_healthy_segment = False

            start_found = False

            healthy_lines = []
            unhealthy_lines = []


            for idx in crop_row.index:
                vegetation = crop_row.at[idx, "vegetation"]

                # skip the beginning of the crop row until the first healthy vegetation point is found
                if not start_found and vegetation <= self.vegetation_threshold:
                    start = idx
                    start_found = True
                    in_healthy_segment = True

                    # if the first point is not healthy, add the line from the start of the crop row to the first healthy point as unhealthy vegetation
                    if start != crop_row.index[0]: 
                        start_point = crop_row[crop_row.index == crop_row.index[0]][["x", "y"]].to_numpy()[0]
                        middle_point = crop_row[crop_row.index == start][["x", "y"]].to_numpy()[0]
                        unhealthy_lines.append([[start_point[0], start_point[1]], [middle_point[0], middle_point[1]]])
                    continue

                if vegetation <= self.vegetation_threshold:
                    if not in_healthy_segment:
                        middle_point = crop_row[crop_row.index == middle][["x", "y"]].to_numpy()[0]
                        end_point = crop_row[crop_row.index == end][["x", "y"]].to_numpy()[0]
                        distance = np.linalg.norm(middle_point - end_point)
                        if distance >= self.unhealthy_vegetation_length:
                            start_point = crop_row[crop_row.index == start][["x", "y"]].to_numpy()[0]
                            healthy_lines.append([[start_point[0], start_point[1]], [middle_point[0], middle_point[1]]])
                            unhealthy_lines.append([[middle_point[0], middle_point[1]], [end_point[0], end_point[1]]])

                            start = idx

                    in_healthy_segment = True
                else:
                    if in_healthy_segment:
                        middle = idx - 1
                    end = idx

                    in_healthy_segment = False
            
            if start_found:
                if in_healthy_segment:
                    start_point = crop_row[crop_row.index == start][["x", "y"]].to_numpy()[0]
                    end_point = crop_row[crop_row.index == crop_row.index[-1]][["x", "y"]].to_numpy()[0]
                    healthy_lines.append([[start_point[0], start_point[1]], [end_point[0], end_point[1]]])
                else:
                    start_point = crop_row[crop_row.index == start][["x", "y"]].to_numpy()[0]
                    middle_point = crop_row[crop_row.index == middle][["x", "y"]].to_numpy()[0]
                    healthy_lines.append([[start_point[0], start_point[1]], [middle_point[0], middle_point[1]]])
                    end_point = crop_row[crop_row.index == end][["x", "y"]].to_numpy()[0]
                    unhealthy_lines.append([[middle_point[0], middle_point[1]], [end_point[0], end_point[1]]])
            
            # Write the healthy and unhealthy lines while keeping the crop row id as attribute
            if len(healthy_lines) != 0:
                if self.output_path_healthy_vegetation_segments is not None:
                    writer_healthy.line(healthy_lines)
                    writer_healthy.record(int(crop_row_id))
            if len(unhealthy_lines) != 0:
                if self.output_path_unhealthy_vegetation_segments is not None:
                    writer_unhealthy.line(unhealthy_lines)
                    writer_unhealthy.record(int(crop_row_id))
            
        if self.output_path_healthy_vegetation_segments is not None:
            writer_healthy.close()
        if self.output_path_unhealthy_vegetation_segments is not None:
            writer_unhealthy.close()

            
                

    def main(self, path_row_information: str, path_points_in_rows: str) -> None:

        row_information = timeit(self.load_csv)(path_row_information)
        
        tiles = timeit(self.seperate_row_information_to_tile)(row_information)
        
        grid = timeit(self.create_tile_grid)(row_information, tiles)
        
        timeit(self.connect_rows_in_tiles)(grid, tiles)
        

        timeit(self.ccrc.sort_connected_crop_rows)()

        timeit(self.ccrc.check_dublicates)()

        
        if self.output_path_connected_crop_rows is not None:
            timeit(self.connected_crop_rows_to_csv)(self.ccrc.connected_crop_rows)
            

        DF_crop_rows_new = timeit(self.merge_all_points_in_all_crop_rows_remove)(
            self.ccrc.connected_crop_rows, path_points_in_rows, row_information, tiles
        )

        if self.output_path_healthy_vegetation_segments is not None or self.output_path_unhealthy_vegetation_segments is not None:
            timeit(self.seperate_healthy_and_unhealthy_vegetation_segments)(DF_crop_rows_new)

    def save_statistics(self, stat_path, args, tiles):
        """
        Save the statistics of the run to a file
        """

        print(f'Writing statistics to the folder "{stat_path}"')

        with open(stat_path + "/output_file.txt", "w") as f:
            f.write("Input parameters:\n")
            f.write(f" - Segmented Orthomosaic: {args.segmented_orthomosaic}\n")
            f.write(f" - Orthomosaic: {args.orthomosaic}\n")
            f.write(f" - Tile sizes: {args.tile_size}\n")
            f.write(f" - Output tile location: {args.output_tile_location}\n")
            f.write(f" - Generated debug images: {args.generate_debug_images}\n")
            f.write(f" - Tile boundary: {args.tile_boundary}\n")
            f.write(
                f" - Ecpected crop row distance: {args.expected_crop_row_distance}\n"
            )
            f.write(
                f" - Date and time of execution: {datetime.now().replace(microsecond=0)}\n"
            )
            f.write("\n\nOutput from run\n")
            f.write(f" - Number of tiles: {len(tiles)}\n")
