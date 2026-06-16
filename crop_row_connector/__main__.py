import argparse
import os

import crop_row_connector.combine_crop_rows as Combine_crop_rows



parser = argparse.ArgumentParser(description='Combine crop rows')
parser.add_argument(
    "path_row_information", 
    type=str, 
    help='Path to the csv file containing the general information af the crop rows '
     '(tile number, tile position, row angle, row number, x1, y1, x2, y2 (start and end point of the row in the tile))'
)
parser.add_argument(
    "path_points_in_rows",
    type=str,
    help='Path to the csv file containing each point in the crop rows and their amount of vegetation '
     '(tile number, row number, x, y, vegetation)'
)
parser.add_argument(
    "--output_path_connected_crop_rows",
    default=None,
    type=str,
    help='Path to the output file, containing which crop rows where connected and from which tiles'
     'This is optional, if not provided, the connected crop rows will not be saved'
)
parser.add_argument(
    "--output_path_vegetation_points",
    default=None,
    type=str,
    help='Path to the output file, containing the points of the vegetation in the crop rows'
     'This is optional, if not provided, the vegetation points will not be saved'
)
parser.add_argument(
    "--output_path_healthy_vegetation_segments",
    default=None,
    type=str,
    help='Path to the output file, containing the points of the healthy vegetation in the crop rows'
     'This is optional, if not provided, the healthy vegetation points will not be saved'
)
parser.add_argument(
    "--output_path_unhealthy_vegetation_segments",
    default=None,
    type=str,
    help='Path to the output file, containing the points of the unhealthy vegetation in the crop rows'
     'This is optional, if not provided, the unhealthy vegetation points will not be saved'
)
parser.add_argument(
    "--angle_tolerance",
    default=0.1,
    type=float,
    help='Angle tolerance for two crop rows to be connected'
)
parser.add_argument(
    "--distance_tolerance",
    default=0.1,
    type=float,
    help='Distance tolerance for two crop rows to be connected'
)
parser.add_argument(
    "--vegetation_threshold",
    default=127,
    type=float,
    help='Vegetation threshold for a point to be considered healthy vegetation'
)
parser.add_argument(
    "--unhealthy_vegetation_length",
    default=0.1,
    type=float,
    help="Length tolerance for unhealthy vegetation in the crop rows"
)
parser.add_argument(
    "--max_workers",
    default=os.cpu_count(),
    type=int,
    help="Set the maximum number of workers. Default to number of cpus.",
)

def _main():
    args = parser.parse_args()
    ccr = Combine_crop_rows.Combine_crop_rows()
    ccr.angle_tolerance = args.angle_tolerance
    ccr.vegetation_threshold = args.vegetation_threshold
    ccr.unhealthy_vegetation_length = args.unhealthy_vegetation_length
    ccr.ccbt.distance_tolerance = args.distance_tolerance
    ccr.output_path_connected_crop_rows = args.output_path_connected_crop_rows
    ccr.output_path_healthy_vegetation_segments = args.output_path_healthy_vegetation_segments
    ccr.output_path_unhealthy_vegetation_segments = args.output_path_unhealthy_vegetation_segments
    ccr.output_path_vegetation_points = args.output_path_vegetation_points
    ccr.max_workers = args.max_workers
    Combine_crop_rows.timeit(ccr.main)(args.path_row_information, args.path_points_in_rows)

if __name__ == "__main__":
    _main()
