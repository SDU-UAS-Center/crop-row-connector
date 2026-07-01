Crop Row Connector
==================

**Connect fragmented crop rows into continuous lines.**

*crop-row-connector* is a Python package that solves a critical problem in precision agriculture:

When large orthomosaic images are processed tile-by-tile, crop rows that span multiple tiles get detected as separate fragments.

This tool reconnects these fragments creating complete crop row geometries for field analysis.

.. figure:: _static/figures/Field_detected.png

    Detected crop rows in an orthomosaic field.

**Use crop-row-connector if you:**

- Use `Crop Row Detector <https://github.com/henrikmidtiby/CropRowDetector>`_ for row detection
- Process agricultural imagery in tiles
- Need to reconstruct complete crop row geometry
- Want to analyze vegetation health along continuous rows

Quick Start
-----------

To install crop-row-connector:

.. code-block:: shell

    pip install crop-row-connector

Running crop-row-connector:

.. code-block:: shell

    crop-row-connector \
        path/to/row_information_global.csv \
        path/to/points_in_rows.csv \
        --distance_tolerance 0.12 \
        --angle_tolerance 0.12 \
        --output_path_connected_crop_rows path/to/connected_crop_rows.csv \
        --output_path_vegetation_points path/to/line_points.csv \
        --output_path_unhealthy_vegetation_segments path/to/unhealthy.shp \
        --output_path_healthy_vegetation_segments path/to/healthy.shp


See `Tutorial with Test Data <1_tutorials/running_the_test_dataset.rst>`_ for a introduction tutorial on how to use the tool.

Documentation Overview
----------------------

This documentation is organized into four sections to help you learn and use crop-row-connector effectively:

**Tutorials** — *Learn by doing*
    Step-by-step guides that walk through practical examples. Start here if you're new to the tool.

    - `Run crop-row-connector on the included test data to see how it works <tutorials/running_the_test_dataset.rst>`_

**How-To Guides** — *Solve specific problems*
    Practical recipes for common tasks when building interfaces or analyzing your own data.

    - `Prepare and validate your field data <how_to/preparing_your_data.rst>`_
    - `Find the right tolerance values for your equipment <2_how_to/choose_connection_parameters.rst>`_
    - `Integrate crop-row-connector into your applications <2_how_to/using_as_library.rst>`_

**Explanation** — *Understand the concepts*
    Conceptual guides that explain how and why crop row connection works.

    - `How the connection algorithm works under the hood <4_explanation/algorithm_overview.rst>`_

**Reference** — *Look up details*
    Technical API documentation for developers integrating the tool into applications.

    - `Complete API documentation for all classes and methods <3_reference/api_reference.rst>`_

Installation
------------

*crop-row-connector* is a python package and can be installed with pip:

.. code-block:: shell

   pip install CDC

See :doc:`Installation <installation>` for more advanced methods of installation.

Acknowledgement
---------------

the *crop-row-connector* tool was developed by SDU UAS Center as part of the project *Præcisionsfrøavl*, that was supported by the `Green Development and Demonstration Programme (GUDP) <https://gudp.lbst.dk/>`_ and `Frøafgiftsfonden <https://froeafgiftsfonden.dk/>`_ both from Denmark.

Index
-----

.. toctree::
   :maxdepth: 2

   installation
   tutorials_guides
   how_to
   reference
   CLI
   contributing
   notes
   2_how_to/preparing_your_data
   2_how_to/choose_connection_parameters
   2_how_to/using_as_library
   4_explanation/algorithm_overview
   3_reference/api_reference
