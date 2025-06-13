# Run these commands in an interactive session to compress your HDF5 files

module load hdf5/1.12.1-fasrc01 # Load HDF5 module
h5repack -v -l CHUNK=1024 file1 file2 GZIP=5 # Set file1 as input, file2 as output; set compression level 1(most) - 9(least)