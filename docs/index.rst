.. ephys2 documentation master file, created by
   sphinx-quickstart on Mon May 16 09:42:49 2022.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

==================================
Welcome to ephys2's documentation!
==================================

.. include:: ./install.rst
   :start-after: install-nompi-begin
   :end-before: install-nompi-end

.. toctree::
   :maxdepth: 1
   :caption: About

   overview
   pipelines
   processing_stages

.. toctree::
   :maxdepth: 1
   :caption: Usage

   cluster
   built_examples/index
   built_stages/index
   gui
   sorting_performance
   errors
   benchmarks

.. toctree::
   :maxdepth: 1
   :caption: Developer reference

   dev
   data_structures
   implementing_stage
   references

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
