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

**1. Clone the Repository:**

If you haven't already, clone the *crop-row-connector* repository from GitHub to your local machine.

.. code-block:: shell

    git clone https://github.com/Stormlord2001/crop-row-connector.git
    cd crop-row-connector

**2. Create a Virtual Environment:**

It is recommended to create a virtual environment to manage dependencies.

.. code-block:: shell

    python3 -m venv venv
    source venv/bin/activate  # On Windows use `venv\Scripts\activate`

**3. Install Dependencies:**

Install the required dependencies into the virtual environment using pip.

.. code-block:: shell

    pip install .

**4. Run the Connector:**

Use the following command to run the *crop-row-connector* with the test data.

.. code-block:: shell

    crop-row-connector docs/test_dataset/input/row_information_global.csv docs/test_dataset/input/points_in_rows.csv --output_path_connected_crop_rows docs/test_dataset/output/connected_crop_rows.csv --output_path_vegetation_points docs/test_dataset/output/line_points.csv --distance_tolerance 0.12 --angle_tolerance 0.12 --output_path_unhealthy_vegetation_segments docs/test_dataset/output/unhealthy --output_path_healthy_vegetation_segments docs/test_dataset/output/healthy

**5. View the Results:**

After running the command, you will find the output files in the specified paths. You can visualize the connected crop rows and line points using georeferencer tools like QGIS.

For more detailed setup instructions, see `Installation <installation.rst>`_.

Documentation Overview
======================

This documentation is organized into four sections to help you learn and use crop-row-connector effectively:

**Tutorials** — *Learn by doing*
    Step-by-step guides that walk through practical examples. Start here if you're new to the tool.

    - `Run the included test data to see how it works <1_tutorials/running_the_test_dataset.rst>`_

**How-To Guides** — *Solve specific problems*
    Practical recipes for common tasks when building interfaces or analyzing your own data.

    - `Prepare and validate your field data <2_how_to/preparing_your_data.rst>`_
    - `Find the right tolerance values for your equipment <2_how_to/choose_connection_parameters.rst>`_
    - `Integrate crop-row-connector into your applications <2_how_to/using_as_library.rst>`_

**Explanation** — *Understand the concepts*
    Conceptual guides that explain how and why crop row connection works.

    - `How the connection algorithm works under the hood <4_explanation/algorithm_overview.rst>`_

**Reference** — *Look up details*
    Technical API documentation for developers integrating the tool into applications.

    - `Complete API documentation for all classes and methods <3_reference/api_reference.rst>`_

Installation
============

*crop-row-connector* is a combined Rust and Python package. Install it easily with pip:

.. code-block:: shell

    python -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    pip install crop-row-connector

For system-wide installation or development setup, see `Installation <installation.rst>`_.

For Engineers Building Farmer Interfaces
=========================================

If you're building a user interface or operation management system for farmers, the tool integrates as a library:

**Start with**: `Using as a Library <2_how_to/using_as_library.rst>`_

The guide includes patterns for:
- Web service endpoints
- Desktop GUI applications  
- Batch field processing
- Parameter optimization workflows

**Then explore**: `Algorithm Overview <4_explanation/algorithm_overview.rst>`_ to understand what parameters mean

This helps you build interfaces that let farmers understand and control the connection process.

For Agricultural Researchers
=============================

If you're analyzing field data or conducting research:

**Start with**: `Run the Test Dataset <1_tutorials/running_the_test_dataset.rst>`_ and `Algorithm Overview <4_explanation/algorithm_overview.rst>`_

**Then use**: `Choose Connection Parameters <2_how_to/choose_connection_parameters.rst>`_ to optimize for your specific equipment

**Reference**: `API Reference <3_reference/api_reference.rst>`_ for detailed technical specifications

Table of Contents
=================

.. toctree::
   :hidden:

   Installation <installation>
   1_tutorials/running_the_test_dataset
   2_how_to/preparing_your_data
   2_how_to/choose_connection_parameters
   2_how_to/using_as_library
   4_explanation/algorithm_overview
   3_reference/api_reference

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

