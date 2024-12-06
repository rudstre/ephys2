import glob
from ephys2.validate import *

fs = glob.glob('../examples/*.yaml')

for f in fs:
	try:
		get_mem_usage(f, 32, 32, 256)
	except:
		print(f)
		raise