"""Main function for cli."""

import argparse
import os
from pathlib import Path

from crop_row_connector.combine_crop_rows import CombineCropRows

parser = argparse.ArgumentParser(description="Combine crop rows")
parser.add_argument(
    "path_row_information",
    type=str,
    help="Path to the csv file containing the general information af the crop rows "
    "(tile number, tile position, row angle, row number, x1, y1, x2, y2 (start and end point of the row in the tile))",
)
parser.add_argument(
    "path_points_in_rows",
    type=str,
    help="Path to the csv file containing each point in the crop rows and their amount of vegetation "
    "(tile number, row number, x, y, vegetation)",
)
parser.add_argument(
    "--output_path_connected_crop_rows",
    default=None,
    type=Path,
    help="Path to the output file, containing which crop rows where connected and from which tiles"
    "This is optional, if not provided, the connected crop rows will not be saved",
)
parser.add_argument(
    "--output_path_vegetation_points",
    default=None,
    type=Path,
    help="Path to the output file, containing the points of the vegetation in the crop rows"
    "This is optional, if not provided, the vegetation points will not be saved",
)
parser.add_argument(
    "--output_path_healthy_vegetation_segments",
    default=None,
    type=Path,
    help="Path to the output file, containing the points of the healthy vegetation in the crop rows"
    "This is optional, if not provided, the healthy vegetation segments will not be saved",
)
parser.add_argument(
    "--output_path_unhealthy_vegetation_segments",
    default=None,
    type=Path,
    help="Path to the output file, containing the points of the unhealthy vegetation in the crop rows"
    "This is optional, if not provided, the unhealthy vegetation segments will not be saved",
)
parser.add_argument(
    "--angle_tolerance",
    default=0.1,
    type=float,
    help="Angle tolerance for two crop rows to be connected. Measured in radians.",
)
parser.add_argument(
    "--distance_tolerance",
    default=0.1,
    type=float,
    help="Distance tolerance for two crop rows to be connected. Measured in meters.",
)
parser.add_argument(
    "--vegetation_threshold",
    default=127,
    type=float,
    help="Vegetation threshold for a point to be considered healthy vegetation. Measured in grayscale values from 0 to 255.",
)
parser.add_argument(
    "--min_unhealthy_vegetation_length",
    default=0.1,
    type=float,
    help="Minimum length tolerance for unhealthy vegetation in the crop rows, to be considered as a segment of unhealthy vegetation. Measured in meters.",
)
parser.add_argument(
    "--max_segment_length",
    default=5,
    type=float,
    help="Maximum length of segments to be considered for vegetation classification. Measured in meters.",
)
parser.add_argument(
    "--max_workers",
    default=os.cpu_count(),
    type=int,
    help="Set the maximum number of workers. Default to number of cpus.",
)


def _main() -> None:
    args = parser.parse_args()
    ccr = CombineCropRows()
    ccr.angle_tolerance = args.angle_tolerance
    ccr.vegetation_threshold = args.vegetation_threshold
    ccr.min_unhealthy_vegetation_length = args.min_unhealthy_vegetation_length
    ccr.max_segment_length = args.max_segment_length
    ccr.ccbt.distance_tolerance = args.distance_tolerance
    ccr.output_path_connected_crop_rows = args.output_path_connected_crop_rows
    ccr.output_path_healthy_vegetation_segments = args.output_path_healthy_vegetation_segments
    ccr.output_path_unhealthy_vegetation_segments = args.output_path_unhealthy_vegetation_segments
    ccr.output_path_vegetation_points = args.output_path_vegetation_points
    ccr.max_workers = args.max_workers
    ccr.main(args.path_row_information, args.path_points_in_rows)


if __name__ == "__main__":
    _main()
