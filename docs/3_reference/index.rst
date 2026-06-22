.. _reference:

=========
Reference
=========

**Look up details** — Complete technical API documentation for developers.

Use these guides when you need to know the exact specification of classes, methods, parameters, and data formats.

.. toctree::
   :maxdepth: 2

   api_reference

What's in Reference
===================

**API Reference**
   - Core classes: ``Combine_crop_rows``, ``find_connection_of_rows_between_two_tiles``, ``combine_crop_rows_from_connections``
   - Methods and attributes for each class
   - Input file formats and requirements
   - Output file formats and structure

When to Use Reference
=====================

Use reference documentation when you:

- **Write code**: Need exact parameter names and types
- **Debug errors**: Want to understand error messages or unusual behavior
- **Integrate libraries**: Building applications that use crop-row-connector
- **Verify specifications**: Checking what a method returns or requires

Reference vs. How-to
====================

**How-to Guide** shows you how to accomplish something with examples.

**Reference** provides technical specifications and details.

- How-to: "To process a field, create a Combine_crop_rows object and call main()"
- Reference: "main(path_row_information: str, path_points_in_rows: str) -> None"

Reference vs. Explanation
==========================

**Explanation** helps you understand why things work the way they do.

**Reference** tells you what things are.

- Explanation: "Understanding how distance tolerance works as a geometric measurement"
- Reference: "distance_tolerance (float, units: meters) - maximum allowed distance between row endpoints"

If You Don't Find Something
============================

- **Looking for how to do something?** → Try `How-to Guides <../2_how_to/index.rst>`_
- **Looking for conceptual understanding?** → Try `Explanation <../4_explanation/index.rst>`_
- **Looking for setup instructions?** → Try `Installation <../installation.rst>`_
- **Learning by example?** → Try `Tutorials <../1_tutorials/index.rst>`_
