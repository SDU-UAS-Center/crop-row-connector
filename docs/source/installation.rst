.. _installation:

Installation
============

*crop-row-connector* is a python package and can be installed with pip or similar:

.. code-block:: shell

    pip install crop-row-connector

It has the following main dependencies:

* numpy
* pandas
* opencv-python
* tqdm
* matplotlib
* pyshp

If the latest version is desired *crop-row-connector* can also be installed directly from git by cloning the repository. We recommend using `uv <https://docs.astral.sh/uv/>`_ to install:

.. code-block:: shell

    uv sync --reinstall

This will install all dependencies and compile the rust code.
