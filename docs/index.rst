Crop Row Connector
==================

**Connect fragmented crop rows into continuous lines.**

*crop-row-connector* is a Python/Rust package that solves a critical problem in precision agriculture: 
when large orthomosaic images are processed tile-by-tile, crop rows that span multiple tiles get detected 
as separate fragments. This tool reconnects these fragments creating complete crop row geometries for field analysis.

.. image:: figures/Field_detected.png
   :alt: Detected crop rows in an orthomosaic field

**Use crop-row-connector if you:**

- Process agricultural imagery in tiles
- Use `Crop Row Detector <https://github.com/henrikmidtiby/CropRowDetector>`_ for row detection
- Need to reconstruct complete crop row geometry
- Want to analyze vegetation health along continuous rows

Quick Start
===========

**1. Install the package:**

.. code-block:: shell

    pip install crop-row-connector

**2. Prepare your data:**

- Row information CSV (from Crop Row Detector)
- Vegetation points CSV (from Crop Row Detector)

**3. Process:**

.. code-block:: python

    from crop_row_connector import combine_crop_rows
    
    ccr = combine_crop_rows.Combine_crop_rows()
    ccr.angle_tolerance = 0.1
    ccr.distance_tolerance = 0.12
    ccr.output_path_connected_crop_rows = "output.csv"
    
    ccr.main("row_information.csv", "vegetation_points.csv")

See :ref:`installing <installation>` for detailed setup instructions.

Documentation Overview
======================

This documentation is organized into four sections to help you learn and use crop-row-connector effectively:

**Tutorials** — *Learn by doing*
    Step-by-step guides that walk through practical examples. Start here if you're new to the tool.

    - :doc:`./1_tutorials/running_the_test_dataset` — Run the included test data to see how it works

**How-To Guides** — *Solve specific problems*
    Practical recipes for common tasks when building interfaces or analyzing your own data.

    - :doc:`2_how_to/preparing_your_data` — Prepare and validate your field data
    - :doc:`2_how_to/choose_connection_parameters` — Find the right tolerance values for your equipment
    - :doc:`2_how_to/using_as_library` — Integrate crop-row-connector into your applications

**Explanation** — *Understand the concepts*
    Conceptual guides that explain how and why crop row connection works.

    - :doc:`4_explanation/algorithm_overview` — How the connection algorithm works under the hood

**Reference** — *Look up details*
    Technical API documentation for developers integrating the tool into applications.

    - :doc:`3_reference/api_reference` — Complete API documentation for all classes and methods

Installation
============

*crop-row-connector* is a combined Rust and Python package. Install it easily with pip:

.. code-block:: shell

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install crop-row-connector

For system-wide installation or development setup, see :ref:`installation <installation>`.

For Engineers Building Farmer Interfaces
=========================================

If you're building a user interface or operation management system for farmers, the tool integrates as a library:

**Start with**: :doc:`how_to/using_as_library`

The guide includes patterns for:
- Web service endpoints
- Desktop GUI applications  
- Batch field processing
- Parameter optimization workflows

**Then explore**: :doc:`explanation/algorithm_overview` to understand what parameters mean

This helps you build interfaces that let farmers understand and control the connection process.

For Agricultural Researchers
=============================

If you're analyzing field data or conducting research:

**Start with**: :doc:`tutorials/running_the_test_dataset` and :doc:`explanation/algorithm_overview`

**Then use**: :doc:`how_to/choose_connection_parameters` to optimize for your specific equipment

**Reference**: :doc:`reference/api_reference` for detailed technical specifications

Table of Contents
=================

.. toctree::
   :hidden:

   Installation <installation>
   tutorials/running_the_test_dataset
   how_to/preparing_your_data
   how_to/choose_connection_parameters
   how_to/using_as_library
   explanation/algorithm_overview
   reference/api_reference

Key Concepts
============

**Tiles and Fragments**
    Large orthomosaic images are divided into smaller tiles for processing. When crop rows cross tile boundaries, 
    they appear as separate fragments in each tile's results.

**Connection**
    The process of matching row fragments across tile boundaries and merging them into continuous crops rows 
    that span the entire field.

**Tolerances**
    Parameters that control when fragments are considered connected:
    
    - **distance_tolerance**: Maximum gap between row endpoints (meters)
    - **angle_tolerance**: Maximum angle difference between rows (radians)

**Hungarian Algorithm**
    The mathematical foundation for matching rows between tiles. It finds the optimal assignment that minimizes 
    connection errors.

Support
=======

- **GitHub Repository**: https://github.com/Stormlord2001/crop-row-connector
- **Issues**: Report bugs or request features on GitHub
- **Questions**: Check the documentation or open a discussion

License
=======

See LICENSE file for licensing information.

