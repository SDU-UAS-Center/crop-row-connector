=======================
Preparing Your Data
=======================

Getting Data Ready for crop-row-connector
==========================================

This guide walks through preparing real field data for processing with *crop-row-connector*.

Data Sources
============

Your data comes from:

1. **Crop Row Detector** (prerequisite tool)
   - Processes orthomosaic imagery
   - Outputs row geometry data
   
2. **Orthomosaic Image** (optional for visualization)
   - GeoTIFF format (.tif)
   - Used with QGIS for verification

3. **Field Survey Data** (if available)
   - Ground control points
   - GPS coordinates
   - Can improve accuracy

Required Input: Row Information CSV
===================================

This file contains detected crop row segments from Crop Row Detector.

File Structure
--------------

**Required Columns** (in any order):

.. code-block:: csv

    tile_number,x_position,y_position,angle,row,x_start,y_start,x_end,y_end
    1,0,0,1.5708,0,100.5,50.2,100.5,150.3
    1,0,0,1.5708,1,105.2,49.8,105.2,149.9
    2,1,0,1.5708,0,205.1,51.0,205.1,151.2

**Column Definitions**:

- **tile_number**: Integer ID unique within this field (typically sequential: 1, 2, 3, ...)
- **x_position**: Tile X coordinate in the field grid
- **y_position**: Tile Y coordinate in the field grid
- **angle**: Crop row direction in radians (typically 0 to 2π)
- **row**: Row number within this tile (unique per tile)
- **x_start**: X coordinate of row segment start (in meters or field units)
- **y_start**: Y coordinate of row segment start
- **x_end**: X coordinate of row segment end
- **y_end**: Y coordinate of row segment end

Validating Row Information
--------------------------

Before processing, validate your data:

.. code-block:: python

    import pandas as pd
    import numpy as np
    
    def validate_row_data(csv_file):
        """Validate row information CSV file."""
        df = pd.read_csv(csv_file)
        
        # Check required columns
        required = ['tile_number', 'x_position', 'y_position', 'angle', 
                   'row', 'x_start', 'y_start', 'x_end', 'y_end']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        
        # Check data types
        print(f"Total rows: {len(df)}")
        print(f"Unique tiles: {df['tile_number'].nunique()}")
        print(f"Unique rows per tile: {df.groupby('tile_number')['row'].nunique().max()}")
        
        # Check for invalid values
        invalid_angles = df[(df['angle'] < 0) | (df['angle'] > 2*np.pi)]
        if len(invalid_angles) > 0:
            print(f"WARNING: {len(invalid_angles)} rows with invalid angles")
        
        # Check for zero-length rows
        zero_length = df[(df['x_start'] == df['x_end']) & 
                         (df['y_start'] == df['y_end'])]
        if len(zero_length) > 0:
            print(f"WARNING: {len(zero_length)} rows with zero length (should be removed)")
        
        # Check tile grid continuity
        tiles = df.groupby('tile_number')[['x_position', 'y_position']].first()
        print(f"\nTile grid coverage:")
        print(tiles)
        
        return df
    
    # Usage
    df = validate_row_data("row_information.csv")

Cleaning Row Data
-----------------

Common data quality issues and fixes:

.. code-block:: python

    import pandas as pd
    
    def clean_row_data(csv_file):
        """Clean row information data."""
        df = pd.read_csv(csv_file)
        
        # Remove duplicate rows
        print(f"Before: {len(df)} rows")
        df = df.drop_duplicates()
        print(f"After removing duplicates: {len(df)} rows")
        
        # Remove zero-length rows
        df = df[~((df['x_start'] == df['x_end']) & 
                  (df['y_start'] == df['y_end']))]
        print(f"After removing zero-length rows: {len(df)} rows")
        
        # Remove NaN values
        initial_len = len(df)
        df = df.dropna()
        if len(df) < initial_len:
            print(f"Removed {initial_len - len(df)} rows with missing values")
        
        # Validate angle range
        df = df[(df['angle'] >= 0) & (df['angle'] <= 2*3.14159)]
        print(f"After angle validation: {len(df)} rows")
        
        return df
    
    # Usage
    clean_df = clean_row_data("raw_row_information.csv")
    clean_df.to_csv("row_information_clean.csv", index=False)

Required Input: Vegetation Points CSV
======================================

This file contains individual vegetation measurement points from the orthomosaic.

File Structure
--------------

**Required Columns** (in any order):

.. code-block:: csv

    tile_number,row_number,x,y,vegetation
    1,0,100.5,50.2,200
    1,0,100.5,50.5,195
    1,0,100.5,50.8,198
    1,1,105.2,49.8,212

**Column Definitions**:

- **tile_number**: Must match tile numbers from row information
- **row_number**: Row number within tile (must match row_information)
- **x**: X coordinate of point
- **y**: Y coordinate of point
- **vegetation**: Vegetation intensity (0-255 grayscale)
  - 0 = bare soil
  - 255 = dense healthy vegetation
  - 127 = intermediate

Validating Vegetation Points
----------------------------

.. code-block:: python

    import pandas as pd
    
    def validate_vegetation_data(csv_file, row_info_file=None):
        """Validate vegetation points data."""
        df = pd.read_csv(csv_file)
        
        # Check required columns
        required = ['tile_number', 'row_number', 'x', 'y', 'vegetation']
        missing = [col for col in required if col not in df.columns]
        if missing:
            raise ValueError(f"Missing columns: {missing}")
        
        print(f"Total points: {len(df)}")
        print(f"Tiles covered: {df['tile_number'].nunique()}")
        print(f"Rows covered: {df['row_number'].nunique()}")
        
        # Check vegetation range
        veg_min, veg_max = df['vegetation'].min(), df['vegetation'].max()
        print(f"Vegetation range: {veg_min} to {veg_max}")
        if veg_max > 255 or veg_min < 0:
            print("WARNING: Vegetation values outside 0-255 range!")
        
        # Check correspondence with row information if provided
        if row_info_file:
            row_df = pd.read_csv(row_info_file)
            row_info = set(zip(row_df['tile_number'], row_df['row']))
            veg_info = set(zip(df['tile_number'], df['row_number']))
            
            orphan_points = veg_info - row_info
            if orphan_points:
                print(f"WARNING: {len(orphan_points)} points reference non-existent rows")
        
        return df
    
    # Usage
    validate_vegetation_data("vegetation_points.csv", "row_information.csv")

Cleaning Vegetation Data
------------------------

.. code-block:: python

    import pandas as pd
    
    def clean_vegetation_data(csv_file, row_info_file):
        """Clean vegetation points data."""
        df = pd.read_csv(csv_file)
        row_info = pd.read_csv(row_info_file)
        
        # Get valid tile-row combinations
        valid_rows = set(zip(row_info['tile_number'], row_info['row']))
        
        # Remove points for non-existent rows
        initial_len = len(df)
        df['is_valid'] = df.apply(
            lambda x: (x['tile_number'], x['row_number']) in valid_rows,
            axis=1
        )
        df = df[df['is_valid']].drop('is_valid', axis=1)
        print(f"Removed {initial_len - len(df)} orphan points")
        
        # Remove duplicates
        df = df.drop_duplicates()
        
        # Remove invalid vegetation values
        df = df[(df['vegetation'] >= 0) & (df['vegetation'] <= 255)]
        
        return df
    
    # Usage
    clean_veg = clean_vegetation_data("raw_vegetation.csv", "row_information.csv")
    clean_veg.to_csv("vegetation_points_clean.csv", index=False)

Data Format Conversion
======================

Converting from Crop Row Detector Output
-----------------------------------------

If your Crop Row Detector produces a different format:

.. code-block:: python

    import pandas as pd
    
    def convert_from_detector_format(detector_output_file):
        """Convert Crop Row Detector output to required format."""
        df = pd.read_csv(detector_output_file)
        
        # Example: if detector uses (tile_id, row_id, x1, y1, x2, y2, angle_deg)
        result = pd.DataFrame({
            'tile_number': df['tile_id'],
            'x_position': df['tile_x'],  # Assuming available
            'y_position': df['tile_y'],
            'angle': df['angle_deg'] * 3.14159 / 180,  # Convert to radians
            'row': df['row_id'],
            'x_start': df['x1'],
            'y_start': df['y1'],
            'x_end': df['x2'],
            'y_end': df['y2'],
        })
        
        return result
    
    # Usage
    df = convert_from_detector_format("detector_output.csv")
    df.to_csv("row_information.csv", index=False)

Coordinate System Considerations
================================

Understanding Your Coordinates
-------------------------------

Your data can use different coordinate systems:

- **Local Grid**: Tile (x, y) in grid coordinates (0,0 at top-left)
- **Meters**: Absolute position in meters from field origin
- **GPS**: Latitude/longitude (must be converted to meters)
- **Pixels**: Image coordinates (must be georeferenced)

The *crop-row-connector* works with any consistent system **as long as coordinates are in the same system**.

Converting GPS to Meters
------------------------

If your coordinates are GPS and you need meters:

.. code-block:: python

    import pandas as pd
    import math
    
    def gps_to_meters(lat, lon, ref_lat, ref_lon):
        """Convert GPS coordinates to approximate meters from reference point."""
        # Rough conversion for small areas (~1 km radius)
        m_per_degree_lat = 111000  # Meters per degree latitude
        m_per_degree_lon = 111000 * math.cos(math.radians(ref_lat))
        
        x = (lon - ref_lon) * m_per_degree_lon
        y = (lat - ref_lat) * m_per_degree_lat
        return x, y
    
    def convert_gps_to_meters(csv_file, ref_lat, ref_lon):
        """Convert GPS coordinates in CSV to meters."""
        df = pd.read_csv(csv_file)
        
        # Convert start point
        x_start, y_start = gps_to_meters(
            df['lat_start'], df['lon_start'], ref_lat, ref_lon
        )
        
        # Convert end point
        x_end, y_end = gps_to_meters(
            df['lat_end'], df['lon_end'], ref_lat, ref_lon
        )
        
        # Update dataframe
        df['x_start'] = x_start
        df['y_start'] = y_start
        df['x_end'] = x_end
        df['y_end'] = y_end
        
        return df
    
    # Usage: Replace with your field's reference point
    df = convert_gps_to_meters("gps_data.csv", ref_lat=40.2671, ref_lon=-111.6260)
    df.to_csv("row_information.csv", index=False)

Setting Up Your Project Directory
==================================

Recommended File Organization
------------------------------

.. code-block:: text

    my_field_2024/
    ├── input/
    │   ├── row_information.csv      (from Crop Row Detector)
    │   ├── vegetation_points.csv    (from Crop Row Detector or other source)
    │   └── orthomosaic.tif          (optional, for verification)
    ├── output/
    │   ├── connected_crop_rows.csv
    │   ├── vegetation_points.csv
    │   ├── healthy_segments.csv
    │   └── unhealthy_segments.csv
    ├── scripts/
    │   └── process_field.py
    └── README.md

Example Processing Script
--------------------------

.. code-block:: python

    # process_field.py
    from pathlib import Path
    from crop_row_connector import combine_crop_rows
    
    # Setup paths
    field_dir = Path("my_field_2024")
    input_dir = field_dir / "input"
    output_dir = field_dir / "output"
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    # Configure processor
    ccr = combine_crop_rows.Combine_crop_rows()
    ccr.angle_tolerance = 0.1
    ccr.distance_tolerance = 0.12
    ccr.vegetation_threshold = 127
    ccr.min_unhealthy_vegetation_length = 0.1
    ccr.max_segment_length = 5
    
    # Set output paths
    ccr.output_path_connected_crop_rows = str(output_dir / "connected_crop_rows.csv")
    ccr.output_path_vegetation_points = str(output_dir / "vegetation_points.csv")
    ccr.output_path_healthy_vegetation_segments = str(output_dir / "healthy_segments.csv")
    ccr.output_path_unhealthy_vegetation_segments = str(output_dir / "unhealthy_segments.csv")
    
    # Process
    print("Processing field...")
    ccr.main(
        str(input_dir / "row_information.csv"),
        str(input_dir / "vegetation_points.csv")
    )
    print("Complete!")

Quick Checklist
===============

Before processing your field data:

- [ ] Row information CSV has all required columns
- [ ] Vegetation points CSV has all required columns
- [ ] No duplicate rows in either CSV
- [ ] No missing values (NaN) in numeric columns
- [ ] Vegetation values in range 0-255
- [ ] Angles in valid range (0-2π or -π to π)
- [ ] Row numbers consistent with detected rows
- [ ] Coordinates are in a consistent system
- [ ] Output directory exists or will be created
- [ ] No special characters in file paths that could cause issues
