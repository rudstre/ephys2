import MEArec as mr
import pdb

cmf = mr.get_default_cell_models_folder()
params = {
	'rot': 'norot',
	'probe': 'tetrode',
	'ncontacts': 1,
	'det_thresh': 50,
	'n': 10,
}
tempgen = mr.gen_templates(cmf, params=params, parallel=False)
pdb.set_trace()
