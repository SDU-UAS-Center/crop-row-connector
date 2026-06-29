================================
Choosing Connection Parameters
================================

Overview
========

The success of crop row connection depends on choosing appropriate tolerance parameters. This guide helps you select values for your specific field conditions and equipment.

Quick Start
===========

For most agricultural applications, start with these defaults:

.. code-block:: python

    angle_tolerance = 0.1                   # ~5.7 degrees
    distance_tolerance = 0.12               # 12 centimeters
    vegetation_threshold = 127              # Mid-range grayscale
    min_unhealthy_vegetation_length = 0.1   # 10 centimeters
    max_segment_length = 5                  # 5 meters

Then fine-tune based on results (see Testing and Validation section).

Understanding Distance Tolerance
=================================

The ``distance_tolerance`` parameter controls whether rows in adjacent tiles are considered connected.

What It Measures
-----------------

Distance tolerance measures the **perpendicular distance between crop row lines at the endpoints** at tile boundaries. It's the maximum acceptable distance for two rows to be considered the same continuous row.

Setting Distance Tolerance
----------------------------

**Too Large** (e.g., > 0.5 m):

- Risk: False connections
- Symptom: Rows that should be separate get merged
- Example: Two parallel rows 0.8m apart might incorrectly merge
- Impact: Unreliable row IDs for farmer operations

**Too Small** (e.g., < 0.05 m):

- Risk: Missed connections
- Symptom: Continuous rows get split at tile boundaries
- Example: A row with slight offset of 0.15m gets disconnected
- Impact: Fragmented crop data prevents analysis

Factors Affecting Distance Tolerance
--------------------------------------

**Crop Rows Bending**
    Curved rows may require larger tolerance to account for natural offsets due to straigt lines being fitted to curved rows.
    
    - Straight rows: 0.05 - 0.1 m
    - Slightly curved rows: 0.1 - 0.2 m
    - Highly curved rows: 0.2 - 0.3 m

**Tile Processing Accuracy**
    Crop Row Detector consistency affects endpoint placement

**Row Spacing**
    Minimum distance between rows limits tolerance
    
    - Narrow spacing (0.5 m): tolerance ≤ 0.2 m
    - Standard spacing (0.75 m): tolerance ≤ 0.3 m
    - Wide spacing (1.5 m): tolerance ≤ 0.5 m
    
    **Rule of thumb**: tolerance < (row_spacing / 2) to avoid merging adjacent rows

Understanding Angle Tolerance
=============================

The ``angle_tolerance`` parameter controls whether rows in adjacent tiles are **aligned directionally** before considering distance.

What It Measures
-----------------

Angle tolerance measures the **maximum rotation difference** between crop rows in adjacent tiles. It filters out completely misaligned rows before computing distances.

Why Angle Matters
------------------

This is a **sanity check** before measuring distance:

1. Crop rows within a field run in consistent directions
2. Adjacent tiles should have similar row angles (or exactly the same in most cases)
3. Rows at very different angles are **definitely not the same row**
4. This pre-filter avoids expensive distance calculations on impossible matches
5. Ensures that the rows along the edge of the field are not connected to rows in the middle of the field (in case of a field with a rotation)

Setting Angle Tolerance
------------------------

**Too Large** (e.g., > 0.3 rad = 17°):
- Risk: Compares rows that clearly run different directions
- Symptom: May find "connections" across field rotations
- Impact: More false positives in distance matching

**Too Small** (e.g., < 0.02 rad = 1°):
- Risk: Rejects valid connections when angles vary slightly
- Symptom: Misses real connections if detector gives varying angles
- Impact: Fragmented rows at tile boundaries

Recommended Values by Field Type
---------------------------------

**Uniform Field (no row bending)**
    - Typical range: 0.05 - 0.1 rad (2.9 - 5.7 degrees)
    - Example: 0.1 rad - allows natural variation in detector

**Field with Slight Row Bending**
    - Typical range: 0.1 - 0.15 rad (5.7 - 8.6 degrees)
    - Example: 0.12 rad - allows for gradual directional change

**Field with Significant Row Bending**
    - Typical range: 0.2 - 0.3 rad (11.5 - 17 degrees)
    - Example: 0.25 rad - accommodates major field rotations

Vegetation Parameters
=====================

Setting Vegetation Threshold
------------------------------

The ``vegetation_threshold`` (0-255 grayscale) classifies points as healthy or unhealthy vegetation.

**Interpretation**:
   - Pixels **above** threshold → healthy vegetation
   - Pixels **below** threshold → unhealthy vegetation

**Typical Values**:
   - 127: Neutral midpoint - half as healthy, half as unhealthy
   - 30-240: Most common working range
   - <30: Very lenient - most vegetation considered healthy
   - >240: Very strict - most vegetation considered unhealthy (can be used ensures only the dense vegetation is classified as healthy)

**How to Determine the Right Value**:
The value depends on your crop type, growth stage, imaging conditions, and accuracy of the detector. Use the following workflow:

1. Examine your vegetation data to understand the range
2. Consider what "unhealthy" means for your crop
3. General workflow:
   
   - Start with 127 (midpoint)
   - Adjust up or down based on visual inspection of results

Setting min_unhealthy_vegetation_length
---------------------------------------

The ``min_unhealthy_vegetation_length`` (meters) filters out noise from unhealthy vegetation classification.

**Purpose**: Prevent single pixels or small spots from being recorded as "unhealthy segments".

**Recommended Values**: 
   - The value depends on your crop type, spacing between two crops, and desired sensitivity. Use the following workflow:
   - 0.05 m: standard value for sensitive detection
   - Increase if you want to ignore small noise and only record substantial unhealthy segments
   - Decrease or set to zero if you want to capture even the smallest unhealthy segments

Setting max_segment_length
--------------------------

The ``max_segment_length`` (meters) controls spatial resolution of vegetation analysis.
This parameter is often used in curving rows to avoid long segments representing a curved row as a single segment. 

**Interpretation**: Vegetation classification is computed on segments up to this length

**Trade-offs**:
   - **Smaller values** (1-2 m): Rows can be curved and the result will represent the curvature better, but more segments are created
   - **Larger values** (5-10 m): Fewer segments, but can not represent curvature well

**Recommendations**:
   - For most applications, 5 m is a good balance between resolution and performance
   - Decrease the number if it is observed that the segments are too long and do not represent the curvature of the rows well
   - Increase the number if it is observed that the segments are too short and too many segments are created, which can make analysis more difficult

Testing and Validation
======================

Workflow for Finding Optimal Parameters
----------------------------------------

1. **Start with defaults**:
   - distance_tolerance = 0.12 m
   - angle_tolerance = 0.1 rad

2. **Run on data**:
   - Use your ``docs/test_dataset/`` or a small field subset

3. **Inspect results**:
   - Count how many rows were connected
   - Visually check for false merges (rows that shouldn't connect)
   - Visually check for false breaks (rows that should connect but don't)

4. **Adjust and iterate**:
   - Too many false merges? → Lower distance_tolerance
   - Too many false breaks? → Raise distance_tolerance
   - Misaligned connections? → Adjust angle_tolerance

5. **Document findings**:
   - Record your final parameters
   - Note which field/equipment they work for (helps future processing in similar conditions)

Validation Checklist
---------------------

After choosing parameters, validate with these checks:

**Connectivity**
- [ ] Rows that visually appear continuous are connected
- [ ] Rows that visually are parallel but separate are not merged
- [ ] No "orphan" rows (single-segment rows that should connect)

**Correctness**
- [ ] Row count matches expected count
- [ ] Connection pattern makes sense (no impossible connections)
- [ ] Vegetation data properly associated with connected rows

**Stability**
- [ ] Results consistent across different field areas
- [ ] Results consistent if run multiple times
- [ ] Small parameter changes don't cause drastic result changes

Common Issues and Solutions
============================

**Too many rows are being merged**

*Symptoms*: Parallel rows combine into single rows

*Solutions*:
   1. Reduce ``distance_tolerance`` (eg. try 0.08 instead of 0.12)
   2. Check if rows truly are the same (visual inspection)
   3. Verify row spacing > 2 × distance_tolerance

**Rows break at tile boundaries**

*Symptoms*: Continuous rows split into fragments

*Solutions*:
   1. Increase ``distance_tolerance`` (eg. try 0.15 instead of 0.12)
   2. Check equipment accuracy - does it guarantee <tolerance positioning?
   3. Verify angle_tolerance isn't filtering valid rows

**Angle mismatches**

*Symptoms*: "Expected connection" message for misaligned rows

*Solutions*:
   1. Check field for actual rotation
   2. Increase ``angle_tolerance`` if rotation is expected (eg. try 0.15-0.2 rad)
   3. Verify detector is producing consistent angles

**Irregular vegetation classifications**

*Symptoms*: Noise or unrealistic health segments

*Solutions*:
   1. Increase ``min_unhealthy_vegetation_length`` to filter noise
   2. Adjust ``vegetation_threshold`` based on typical crop conditions
   3. Increase ``max_segment_length`` for coarser classification

Example: Optimizing for Your Field
===================================

**Scenario**: Potato field, narrow row spacing (0.2 m)

*Initial parameters*:

.. code-block:: python

    distance_tolerance = 0.15
    angle_tolerance = 0.1

*Test 1 Results*: Adjacent rows merged into single rows

*Analysis*: 0.15 m is too large for 0.2 m spacing

*Adjust*:

.. code-block:: python

    distance_tolerance = 0.04

*Test 2 Results*: Some rows break at tile boundaries

*Analysis*: 0.04 m is too small for drone accuracy

*Final parameters*:

.. code-block:: python

    distance_tolerance = 0.8
    angle_tolerance = 0.1

*Validation*: All rows properly connected with no false merges ✓
