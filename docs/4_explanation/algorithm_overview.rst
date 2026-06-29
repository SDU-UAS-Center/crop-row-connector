===========================
Algorithm Overview
===========================

Understanding Crop Row Connection
===================================

The *crop-row-connector* solves a fundamental problem in agricultural data processing: connecting fragmented crop row detections across tile boundaries.

The Problem
-----------

When processing orthomosaic images of agricultural fields:

1. Large images are divided into smaller **tiles** for processing efficiency
2. Crop Row Detector runs on each tile independently, detecting crop rows within that tile
3. A crop row that spans multiple tiles gets detected as **separate fragments** across tile boundaries
4. These fragments need to be **reconnected** to form continuous crop row lines

Without connection, analysis becomes impossible:
   - Incomplete row geometry
   - Fragmented vegetation data
   - Loss of spatial continuity
   - No overlap handling between tiles

The Solution: Multi-Step Connection Algorithm
----------------------------------------------

*crop-row-connector* reconnects these fragments using a three-stage approach:

Stage 1: Tile Analysis
^^^^^^^^^^^^^^^^^^^^^^^

Each tile is analyzed to extract:
   - **Tile Position**: Location in the field grid (X, Y)
   - **Rows**: Detected crop rows with their endpoints and geometry
   - **Angle**: The predominant direction of crop rows in this tile

This creates a structured representation of row data that can be compared across tiles.

Stage 2: Pairwise Tile Matching (Hungarian Algorithm)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For each pair of neighboring tiles, the algorithm:

1. **Computes a cost matrix**: Measures how well each row in Tile A matches each row in Tile B
   - Distance between rows (in meters)
   - Directional alignment

2. **Applies the Hungarian Algorithm**: Finds the optimal assignment that minimizes total cost
   - Each row matches to at most one row in the adjacent tile
   - Assigns based on geometric proximity and angle compatibility

3. **Filters results**: Removes unlikely connections using **tolerance thresholds**
   - ``distance_tolerance``: Maximum distance between row endpoints
   - ``angle_tolerance``: Maximum angle difference between rows

**Key insight**: This step finds row-to-row correspondences between neighboring tiles.

Stage 3: Global Graph Construction
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Connections from all pairwise matches are merged into a global graph where:
   - **Nodes** are individual row segments (tile + row number)
   - **Edges** represent validated connections
   - **Graph traversal** identifies connected components (complete crop rows)

Result: Fragmented rows become continuous crop row objects, each with:
   - All connected segments across tiles
   - Complete spatial geometry
   - Associated vegetation data points

Geometric Matching Details
============================

How Distance is Calculated
----------------------------

The algorithm measures distance between two rows as:
   1. **Extract endpoints** from both rows (start and end points)
   2. **Identify "close" and "far" endpoints** by finding maximum pairwise distance
   3. **Compute perpendicular distances** from one row's close point to the other row's line
   4. **Average the reciprocal distances** for a symmetric measure

This approach is robust because:
   - It doesn't require exact endpoint alignment
   - It tolerates slight variations in row endpoint positioning
   - It captures whether rows are "roughly parallel and close"

Why Angles Matter
------------------

Crop rows within a field typically run in consistent directions:
   - **Same tile**: All rows share the same angle (field-level property)
   - **Adjacent tiles**: Usually have the same angle
   - **Exception**: Field rotations between tiles (rare but possible, as can be seen in the test dataset)

The ``angle_tolerance`` parameter filters out impossible matches:
   - Rows at completely different angles are unlikely to be the same row
   - Typical tolerance: 0.1 radians (~5.7 degrees)

Parameters and Their Meaning
=============================

Connection Parameters
---------------------

**distance_tolerance** (meters)
    Maximum allowed distance between row endpoints for them to be considered connected.
       - Default: 0.1 m
       - Typical range: 0.05-0.5 m
       - Higher values → more connections (risk of false matches)
       - Lower values → fewer connections (risk of missing real matches)

**angle_tolerance** (radians)
    Maximum allowed angle difference between rows for connection.
       - Default: 0.1 rad (~5.7 degrees)
       - Typical range: 0.05-0.2 rad
       - Higher values → more flexible angle matching
       - Lower values → stricter angular requirements

Vegetation Parameters
---------------------

**vegetation_threshold** (grayscale 0-255)
    Pixel value threshold for classifying vegetation as "healthy".
    
    - Default: 127 (mid-range)
    - Higher values → higher vegetation density needed to be "healthy"
    - Lower values → more pixels classified as healthy

**min_unhealthy_vegetation_length** (meters)
    Minimum spatial extent for unhealthy vegetation to be recorded as a segment.
    
    - Default: 0.1 m
    - Prevents noise from being recorded as disease
    - Filter for biologically meaningful segments

**max_segment_length** (meters)
    Maximum length for vegetation classification segments.
    
    - Default: 5 m
    - Affects spatial resolution of vegetation analysis
    - Larger values → coarser vegetation classification
    - Smaller values → finer vegetation classification

Algorithm Complexity
====================

Performance Considerations
---------------------------

The connection process has complexity roughly proportional to:

- Number of tiles: :math:`N_{tiles}`
- Rows per tile: :math:`R_{avg}`
- Connections per pair: Hungarian Algorithm is :math:`O(R^3)`

For typical agricultural fields:
- 100-1000 tiles
- 10-100 rows per tile
- Processing time: seconds to minutes (depending on field size)

The Rust implementation provides performance-critical operations for:
- Distance calculations
- Hungarian algorithm execution
- Graph traversal and merging

This hybrid Python/Rust design ensures:
- **Usability**: Python interface for configuration and control
- **Performance**: Rust for computationally intensive operations
- **Flexibility**: Easy to experiment with parameters from Python
