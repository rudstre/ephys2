'''
Split an RHD file at a sample index 
'''

from ephys2.lib.intanutil.header import *

in_path = '/Users/anandsrinivasan/dev/fasrc/data/r4_210612_195804.rhd'
out_path = '/Users/anandsrinivasan/dev/fasrc/ephys2/ephys2/tests/data/r4_210612_195804_part.rhd'
n_blocks = 100

with open(in_path, 'rb') as in_file:
	with open(out_path, 'wb') as out_file:
		header = read_header(in_file)
		header_offset = in_file.tell()
		in_file.seek(0)
		header_binary = in_file.read(header_offset)
		out_file.write(header_binary)
		data_offset = get_bytes_per_data_block(header) * n_blocks
		data_binary = in_file.read(data_offset)
		out_file.write(data_binary)

