============
Installation
============

There are two options for building ``ephys2``, one which is suitable for use on your local workstation (for example, using the GUI) and the second which is suitable for a cluster environment or developer build.

.. install-nompi-begin
.. _install_nompi:

Install on user workstation (without MPI support)
=================================================

First, clone this repository using 

.. code-block:: console

	$ git clone git@gitlab.com:olveczkylab/ephys2

Then, install `Anaconda <https://www.anaconda.com/products/distribution/>`_ for your system, and activate an environment for ``ephys2``:

.. code-block:: console:

	$ cd ephys2/ephys2
	$ conda env create -f environment.yaml

Finally, build and install the source using:

.. code-block:: console

	$ cd ephys2/ephys2
	$ pip install -r setup-requirements.txt
	$ pip install -U .

If you plan on using the GUI on your local machine, continue following the install instructions at :ref:`install_gui`.

.. install-nompi-end

.. install-mpi-begin

Install on cluster / developer workstation (with MPI support)
=============================================================

.. install-mpi-end