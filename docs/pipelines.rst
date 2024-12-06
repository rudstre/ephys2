=========
Pipelines
=========

Pipelines are declared as `YAML <https://yaml.org/>`_ files, which are transformed internally into a JSON-like structure in Python.

.. code-block:: yaml

	- input.rhd2000:
		sessions: /path/to/file.rhd 
		datetime_pattern: "*_%y%m%d_%H%M%S" 
		batch_size: 450000  
		batch_overlap: 0 
		aux_channels: []

	- preprocess.bandpass:
		order: 4 
		highpass: 300 
		lowpass: 7500 
		Rp: 0.2 
		Rs: 100 
		type: ellip 
		padding_type: odd 
		padding_length: 1000 

	- checkpoint:
		file: /path/to/output.h5
		batch_size: 1000 
		batch_overlap: 0 

This pipeline consists of three :doc:`processing_stages`:

#. An `RHD2000 <https://intantech.com/files/Intan_RHD2000_data_file_formats.pdf>`_ file reader, which will read amplifier data in batches of size 450000.
#. A bandpass filter between 300 and 7500 Hz.
#. A ``checkpoint`` (see :doc:`overview`) which saves the output to ``output.h5`` and produces batches of size 1000 for the next stage.