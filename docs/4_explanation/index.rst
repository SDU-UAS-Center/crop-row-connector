.. _explanation:

===========
Explanation
===========

**Understand the concepts** — These guides explain how and why crop row connection works.

Read these to develop deeper understanding of the tool's design and algorithms. 
Use these to make informed decisions about parameters and approaches.

.. toctree::
   :maxdepth: 2

   algorithm_overview

When to Read Explanation
========================

Read explanation guides when you want to:

- **Understand the algorithm**: Learn how crop rows are matched and connected
- **Make better decisions**: Choose parameters informed by understanding what they do
- **Debug results**: Understand why you're getting particular results
- **Contribute**: Understand the system well enough to contribute improvements
- **Teach others**: Explain how the tool works to colleagues or users

How Explanation Differs from How-to
===================================

**How-to Guides** tell you *how* to accomplish something (recipes).

**Explanation** tells you *why* the system works the way it does (understanding).

- How-to: "Set distance_tolerance to 0.12"
- Explanation: "Distance tolerance is measured in meters between row endpoints, and represents the maximum acceptable gap between fragments for them to be considered connected"

How Explanation Differs from Reference
=======================================

**Reference** provides technical specifications (lookup).

**Explanation** provides context and understanding (learning).

- Reference: "angle_tolerance (float) - angle threshold in radians"
- Explanation: "Angle tolerance acts as a pre-filter before computing distances, because rows at wildly different angles are definitely not the same row, saving computational effort"

Topics Covered
===============

**Algorithm Overview**
    How crop rows are detected as fragments, how the Hungarian algorithm matches fragments, 
    and how these matches are merged into complete crop rows.
