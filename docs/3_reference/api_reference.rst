==================================
API Reference
==================================

Main Classes
============

Combine_crop_rows
------------------

The primary orchestrator class that manages the entire crop row connection process.

**Location**: ``crop_row_connector.combine_crop_rows.Combine_crop_rows``

Configuration Attributes
^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:attribute:: angle_tolerance

    (float) Maximum angle difference in radians for rows to be considered for connection.

    **Type**: float
    **Default**: None (must be set before use)
    **Typical range**: 0.05 - 0.2 radians
    **Units**: Radians (convert degrees: radians = degrees × π/180)

.. py:attribute:: distance_tolerance

    (float) Maximum distance in meters between row endpoints for connection.

    **Type**: float
    **Default**: None (must be set before use)
    **Typical range**: 0.05 - 0.5 meters
    **Units**: Meters

.. py:attribute:: vegetation_threshold

    (float) Grayscale threshold (0-255) for classifying vegetation as healthy.

    **Type**: float
    **Default**: None (must be set before use)
    **Typical range**: 100 - 150
    **Units**: Grayscale intensity (0=black, 255=white)

.. py:attribute:: min_unhealthy_vegetation_length

    (float) Minimum spatial extent in meters for unhealthy vegetation segments to be recorded.

    **Type**: float
    **Default**: None (must be set before use)
    **Typical range**: 0.05 - 0.5 meters
    **Units**: Meters

.. py:attribute:: max_segment_length

    (float) Maximum length in meters for vegetation classification segments.

    **Type**: float
    **Default**: None (must be set before use)
    **Typical range**: 1 - 10 meters
    **Units**: Meters

.. py:attribute:: max_workers

    (int) Maximum number of parallel workers for processing.

    **Type**: int
    **Default**: os.cpu_count() (number of CPU cores)
    **Note**: Affects parallelization for large datasets

Output Path Attributes
^^^^^^^^^^^^^^^^^^^^^^^

All output paths are optional. If None, that output won't be generated.

.. py:attribute:: output_path_connected_crop_rows

    (str or None) Path to save connected crop rows to CSV.

    **Output format**: CSV with columns:
    - row_index: Unique identifier for connected row
    - tile: Tile number
    - row: Row number within tile
    - con_1_tile, con_1_row: First connected row
    - con_2_tile, con_2_row: Second connected row
    - con_3_tile, con_3_row: Third connected row
    - con_4_tile, con_4_row: Fourth connected row
    - dubli_error: Duplicate detection flag

.. py:attribute:: output_path_vegetation_points

    (str or None) Path to save all vegetation points associated with connected rows.

    **Output format**: CSV with coordinates and vegetation values

.. py:attribute:: output_path_healthy_vegetation_segments

    (str or None) Path to save segments with healthy vegetation.

    **Output format**: CSV with spatial location and health metrics

.. py:attribute:: output_path_unhealthy_vegetation_segments

    (str or None) Path to save segments with unhealthy vegetation.

    **Output format**: CSV with spatial location and damage metrics

Core Methods
^^^^^^^^^^^^

.. py:method:: __init__()

    Initialize a new Combine_crop_rows instance with default settings.

    **Returns**: Combine_crop_rows object

    **Example**:

    .. code-block:: python

        ccr = Combine_crop_rows()

.. py:method:: main(path_row_information: str, path_points_in_rows: str) -> None

    Execute the complete crop row connection pipeline.

    **Parameters**:

    - ``path_row_information`` (str): Path to CSV with row information
      Format: [tile_number, x_position, y_position, angle, row, x_start, y_start, x_end, y_end]

    - ``path_points_in_rows`` (str): Path to CSV with vegetation points
      Format: [tile_number, row_number, x, y, vegetation]

    **Raises**: FileNotFoundError if input files don't exist

    **Side effects**: Creates output files at configured paths

    **Example**:

    .. code-block:: python

        ccr = Combine_crop_rows()
        ccr.angle_tolerance = 0.1
        ccr.distance_tolerance = 0.12
        ccr.vegetation_threshold = 127
        ccr.output_path_connected_crop_rows = "output.csv"
        ccr.main("rows.csv", "points.csv")

.. py:method:: load_csv(path: str) -> NDArray[np.float64]

    Load a CSV file into a NumPy array for processing.

    **Parameters**:

    - ``path`` (str): Path to CSV file

    **Returns**: NumPy array of float64 values

    **Raises**: FileNotFoundError, ValueError if CSV is malformed

    **Note**: Automatically converts CSV to numpy format for performance

.. py:method:: ensure_parent_directory_exist(path: Path) -> None

    Ensure that the directory structure for an output file exists.

    **Parameters**:

    - ``path`` (Path): Output file path

    **Side effects**: Creates directories if they don't exist

    **Note**: Called automatically for all output files

find_connection_of_rows_between_two_tiles
-------------------------------------------

Handles the Hungarian algorithm-based matching between adjacent tiles.

**Location**: ``crop_row_connector.find_connection_of_rows_between_two_tiles.find_connection_of_rows_between_two_tiles``

Configuration Attributes
^^^^^^^^^^^^^^^^^^^^^^^^^

.. py:attribute:: distance_tolerance

    (float) Distance threshold for filtering matched rows.

    **Type**: float
    **Units**: Meters

Tracking Attributes
^^^^^^^^^^^^^^^^^^^^

These are read-only counters for debugging and analysis:

.. py:attribute:: removed_connections

    (int) Number of connections rejected for exceeding distance tolerance.

.. py:attribute:: removed_padded_connections

    (int) Number of padding rows/columns removed from Hungarian algorithm output.

Core Methods
^^^^^^^^^^^^

.. py:method:: calculate_connections_between_2_tiles(tile_1: tile, tile_2: tile) -> NDArray

    Find all valid row-to-row connections between two adjacent tiles.

    **Parameters**:

    - ``tile_1`` (tile): First tile object
    - ``tile_2`` (tile): Second tile object

    **Returns**: Connection matrix with shape (n_connections, 2)
    Columns: [row_index_in_tile_1, row_index_in_tile_2]

    **Algorithm**:
    1. Build cost matrix from distances
    2. Apply Hungarian algorithm
    3. Filter with distance tolerance
    4. Remove padding from square matrix

    **Example**:

    .. code-block:: python

        finder = find_connection_of_rows_between_two_tiles()
        finder.distance_tolerance = 0.12
        connections = finder.calculate_connections_between_2_tiles(tile_a, tile_b)
        # connections shape: (n_matches, 2)

combine_crop_rows_from_connections
-------------------------------------

Manages the global graph of crop row connections.

**Location**: ``crop_row_connector.combine_crop_rows_from_connections.combine_crop_rows_from_connections``

Core Methods
^^^^^^^^^^^^

.. py:method:: connect_crop_rows_of_2_tiles(tile_1_number: int, tile_2_number: int, connections: NDArray) -> None

    Apply connections between two tiles to the global crop row graph.

    **Parameters**:

    - ``tile_1_number`` (int): ID of first tile
    - ``tile_2_number`` (int): ID of second tile
    - ``connections`` (NDArray): Connection matrix from Hungarian algorithm

    **Behavior**:
    - If both rows are new: create new connected row entry
    - If one row exists: extend existing connected row
    - If both exist: merge two connected row groups

    **Side effects**: Updates internal connected_crop_rows array

State Attributes
^^^^^^^^^^^^^^^^

.. py:attribute:: connected_crop_rows

    (NDArray) Master array of all connected crop rows.

    **Shape**: (n_connected_rows, 12)
    **Columns**:
    - Index 0: row_index (unique connected row ID)
    - Index 1-2: tile and row number
    - Index 3-4: connected tile and row
    - Index 5-10: Additional connection slots (up to 4 total)
    - Index 11: duplicate error flag

.. py:attribute:: crop_row_index

    (int) Counter for assigning new connected row IDs.

Data Structures
================

tile Object
-----------

Represents a single tile of processed orthomosaic data.

**Attributes**:

- ``tile_number`` (int): Unique identifier for this tile
- ``position`` (list[float]): [x, y] grid position of tile
- ``angle`` (float): Predominant crop row direction in radians
- ``rows`` (NDArray): Detected rows with shape (n_rows, 9)

  Columns in rows array:
  - Index 0: row number
  - Index 1-2: start point (x, y)
  - Index 3-4: end point (x, y)
  - Index 5: additional metadata
  - ...

Input File Formats
===================

Row Information CSV
--------------------

Input file for ``path_row_information`` parameter.

**Required Columns**:

- tile_number: Integer ID of the tile
- x_position: X coordinate of tile in grid
- y_position: Y coordinate of tile in grid
- angle: Crop row angle in radians
- row: Row number within tile
- x_start: Starting X coordinate of row segment
- y_start: Starting Y coordinate of row segment
- x_end: Ending X coordinate of row segment
- y_end: Ending Y coordinate of row segment

**Example CSV**:

.. code-block:: csv

    tile_number,x_position,y_position,angle,row,x_start,y_start,x_end,y_end
    1,0,0,1.57,0,100.5,50.2,100.5,150.3
    1,0,0,1.57,1,105.2,49.8,105.2,149.9
    2,1,0,1.57,0,205.1,51.0,205.1,151.2

Vegetation Points CSV
----------------------

Input file for ``path_points_in_rows`` parameter.

**Required Columns**:

- tile_number: Tile where point was detected
- row_number: Which row within the tile
- x: X coordinate of point
- y: Y coordinate of point
- vegetation: Vegetation intensity (0-255 grayscale)

**Example CSV**:

.. code-block:: csv

    tile_number,row_number,x,y,vegetation
    1,0,100.5,50.2,200
    1,0,100.5,50.5,195
    1,0,100.5,50.8,198

Output File Formats
====================

Connected Crop Rows CSV
------------------------

Generated by ``output_path_connected_crop_rows``.

**Columns**:

- row_index: Unique ID for this connected row
- tile: Tile number
- row: Row number
- con_1_tile, con_1_row: Connection 1
- con_2_tile, con_2_row: Connection 2
- con_3_tile, con_3_row: Connection 3
- con_4_tile, con_4_row: Connection 4
- dubli_error: Duplicate flag (1 if detected)

**Interpretation**: Each connected row may have up to 4 connections to other row segments across tile boundaries.

Vegetation Points CSV
---------------------

Generated by ``output_path_vegetation_points``.

Contains merged and deduplicated vegetation points from all connected rows.

Health/Unhealthy Segments
---------------------------

Generated by ``output_path_healthy_vegetation_segments`` and ``output_path_unhealthy_vegetation_segments``.

Segments are identified based on the configured ``vegetation_threshold`` and ``min_unhealthy_vegetation_length``.
