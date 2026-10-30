.. image:: images/orochi_icon.png
   :align: center
   :width: 80px
   :target: https://github.com/Tominaka-Laboratory/orochi.ui
   :alt: Orochi Logo

=========
orochi.ui
=========

.. |title| replace:: orochi.ui
.. _title: https://Tominaka-Laboratory.github.io/orochi.ui

.. |Icon| image:: images/orochi_icon.png
   :target: https://github.com/Tominaka-Laboratory/orochi.ui
   :height: 100px

|PyPi| |Forge| |PythonVersion| |ChemRxiv| |PR|

|CI| |Codecov| |Black| |Tracking|

.. |ChemRxiv| image:: https://img.shields.io/badge/ChemRxiv-10.26434%2Fchemrxiv.15010802-blue.svg
        :target: https://doi.org/10.26434/chemrxiv.15010802

.. |Black| image:: https://img.shields.io/badge/code_style-black-black
        :target: https://github.com/psf/black

.. |CI| image:: https://github.com/Tominaka-Laboratory/orochi.ui/actions/workflows/tests.yml/badge.svg
        :target: https://github.com/Tominaka-Laboratory/orochi.ui/actions/workflows/tests.yml

.. |Codecov| image:: https://codecov.io/gh/Tominaka-Laboratory/orochi.ui/branch/main/graph/badge.svg
        :target: https://codecov.io/gh/Tominaka-Laboratory/orochi.ui

.. |Forge| image:: https://img.shields.io/conda/vn/conda-forge/orochi.ui
        :target: https://anaconda.org/conda-forge/orochi.ui

.. |PR| image:: https://img.shields.io/badge/PR-Welcome-29ab47ff

.. |PyPi| image:: https://img.shields.io/pypi/v/orochi.ui
        :target: https://pypi.org/project/orochi.ui/

.. |PythonVersion| image:: https://img.shields.io/pypi/pyversions/orochi.ui
        :target: https://pypi.org/project/orochi.ui/

.. |Tracking| image:: https://img.shields.io/badge/issue_tracking-github-blue
        :target: https://github.com/Tominaka-Laboratory/orochi.ui/issues


Overview
========
orochi.ui provides an environment for freely creating task-specific user interfaces. It's designed to manage the flexible parameters controlled by orochi.base and to execute packages built upon them. The core concept behind its development is the automatic generation of tabs for each task.

The execution flow and inter-module relationships are defined in the Python backend, while the UI is displayed in a browser using Gradio. You can generate a UI by simply defining the parameters to be displayed and those used for fitting in the backend. orochi.ui is developed with the philosophy that the UIs provided in orochi.tutorial will suffice for most typical use cases.

For more information about the orochi.ui library, please consult our `online documentation <https://Tominaka-Laboratory.github.io/orochi.ui>`_.

Citation
--------

If you use orochi.ui in a scientific publication, we would like you to cite this package as

        orochi.ui Package, https://github.com/Tominaka-Laboratory/orochi.ui

Installation
------------

The preferred method is to use `Miniconda Python
<https://docs.conda.io/projects/miniconda/en/latest/miniconda-install.html>`_
and install from the "conda-forge" channel of Conda packages.

To add "conda-forge" to the conda channels, run the following in a terminal. ::

        conda config --add channels conda-forge

We want to install our packages in a suitable conda environment.
The following creates and activates a new environment named ``orochi.ui_env`` ::

        conda create -n orochi.ui_env orochi.ui
        conda activate orochi.ui_env

To confirm that the installation was successful, type ::

        python -c "import orochi.pdf_simulator; print(orochi.pdf_simulator.__version__)"

The output should print the latest version displayed on the badges above.

If the above does not work, you can use ``pip`` to download and install the latest release from
`Python Package Index <https://pypi.python.org>`_.
To install using ``pip`` into your ``orochi.ui_env`` environment, type ::

        pip install orochi.ui

If you prefer to install from sources, after installing the dependencies, obtain the source archive from
`GitHub <https://github.com/Tominaka-Laboratory/orochi.ui/>`_. Once installed, ``cd`` into your ``orochi.ui`` directory
and run the following ::

        pip install .

Getting Started
---------------

You may consult our `online documentation <https://Tominaka-Laboratory.github.io/orochi.ui>`_ for tutorials and API references.

Support and Contribute
----------------------

The orochi.ui project welcomes your expertise and enthusiasm!

If you see a bug or want to request a feature, please `report it as an issue <https://github.com/Tominaka-Laboratory/orochi.ui/issues>`_ and/or `submit a fix as a PR <https://github.com/Tominaka-Laboratory/orochi.ui/pulls>`_.

Feel free to fork the project and contribute. To install orochi.ui
in a development mode, with its sources being directly used by Python
rather than copied to a package directory, use the following in the root
directory ::

        pip install -e .

To ensure code quality and to prevent accidental commits into the default branch, please set up the use of our pre-commit
hooks.

Improvements and fixes are always appreciated.

Before contributing, please read our `Code of Conduct <https://github.com/Tominaka-Laboratory/orochi.ui/blob/main/CODE_OF_CONDUCT.rst>`_.



License
-------

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**. See the `LICENSE.rst` file for details.

This copyleft license guarantees that Orochi remains freely accessible, open, and transparent to the entire scientific community, and that all derivative works must likewise remain open source.

Citation
--------

If you use this package in academic research, please cite:

.. code-block:: bibtex

    @article{tominaka2026orochi,
      title   = {Orochi: A Physics-Grounded Python Package for Pair Distribution Function Analysis of Crystalline and Low-Dimensional Materials},
      author  = {Tominaka, Satoshi},
      journal = {ChemRxiv},
      year    = {2026},
      doi     = {10.26434/chemrxiv.15010802},
      url     = {https://doi.org/10.26434/chemrxiv.15010802}
    }

Contact
-------

For more information on orochi.ui please visit the project `web-page <https://Tominaka-Laboratory.github.io/>`_ or email Dr. Satoshi Tominaka at tominaka.satoshi@nims.go.jp.
