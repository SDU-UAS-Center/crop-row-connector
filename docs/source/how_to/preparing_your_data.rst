Preparing Your Data
===================

Getting Data Ready for crop-row-connector
-----------------------------------------

This guide walks through preparing real field data for processing with *crop-row-connector*.

Data Sources
------------

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
-----------------------------------

This file contains detected crop row segments from Crop Row Detector.

File Structure
^^^^^^^^^^^^^^

**Required Columns** (in this order):

=========== ========== ========== ====== === ======= ======= ===== ===== ===== ======
tile_number x_position y_position angle  row x_start y_start x_end y_end x_mid y_mid
=========== ========== ========== ====== === ======= ======= ===== ===== ===== ======
1           0          0          1.5708 0   100.5   50.2    100.5 150.3 100.5 100.25
1           0          0          1.5708 1   105.2   49.8    105.2 149.9 105.2 99.85
2           1          0          1.5708 0   205.1   51.0    205.1 151.2 205.1 101.1
=========== ========== ========== ====== === ======= ======= ===== ===== ===== ======

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
- **x_mid**: X coordinate of row segment midpoint
- **y_mid**: Y coordinate of row segment midpoint

Required Input: Vegetation Points CSV
-------------------------------------

This file contains individual vegetation measurement points from the orthomosaic.

File Structure
^^^^^^^^^^^^^^

**Required Columns** (in this order):

=========== ========== ===== ==== ==========
tile_number row_number x     y    vegetation
=========== ========== ===== ==== ==========
1           0          100.5 50.2 200
1           0          100.5 50.5 195
1           0          100.5 50.8 198
1           1          105.2 49.8 212
=========== ========== ===== ==== ==========

**Column Definitions**:

- **tile_number**: Must match tile numbers from row information
- **row_number**: Row number within tile (must match row_information)
- **x**: X coordinate of point
- **y**: Y coordinate of point
- **vegetation**: Vegetation intensity (0-255 grayscale)

  - 0 = bare soil
  - 255 = dense healthy vegetation
  - 127 = intermediate

Coordinate System Considerations
--------------------------------

Understanding Your Coordinates
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Your data can use different coordinate systems:

- **Local Grid**: Tile (x, y) in grid coordinates (0,0 at top-left)
- **Meters**: Absolute position in meters from field origin
- **GPS**: Latitude/longitude (must be converted to meters)
- **Pixels**: Image coordinates (must be georeferenced)

The *crop-row-connector* works with any consistent system **as long as coordinates are in the same system**.

Setting Up Your Project Directory
---------------------------------

Recommended File Organization
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: text

    my_field/
    ├── input/
    │   ├── row_information.csv      (from Crop Row Detector)
    │   ├── vegetation_points.csv    (from Crop Row Detector or other source)
    │   └── orthomosaic.tif          (optional, for verification)
    └── output/
        ├── connected_crop_rows.csv
        ├── vegetation_points.csv
        ├── healthy_segments.csv
        └── unhealthy_segments.csv

Quick Checklist
---------------

If processing fails ensure the following before processing your field data again:

- [ ] Row information CSV has all required columns
- [ ] Vegetation points CSV has all required columns
- [ ] No duplicate rows in either CSV
- [ ] No missing values (NaN) in numeric columns
- [ ] Vegetation values in range 0-255
- [ ] Angles in valid range (0-2π or -π to π)
- [ ] Row numbers consistent with detected rows
- [ ] Coordinates are in a consistent system
- [ ] No special characters in file paths that could cause issues
