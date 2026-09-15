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

Installing from source
----------------------

If the latest version is desired *crop-row-connector* can also be installed directly from git by cloning the repository. We recommend using `uv <https://docs.astral.sh/uv/>`_ to install:

.. code-block:: shell

    uv sync --reinstall

This will install all dependencies and compile the rust code.

.. note::
    The package contains a Rust extension that is compiled during installation.
    Building from source (including ``pip install .`` from a clone) requires a
    `Rust toolchain <https://rustup.rs/>`_ to be installed. Pre-built wheels are
    available on PyPI for common platforms, so ``pip install crop-row-connector``
    from PyPI does not need Rust.
