import sklearn
import sklearn.datasets
import sklearn.cluster
import numpy as np
import cProfile
import pstats

from ephys2.lib.spc import *

X, y = sklearn.datasets.make_blobs(n_samples=1000, cluster_std=[1.0, 2.5, 0.5], random_state=170)

spc_temps, spc_labelings =  run_spc(
	X, 0, 0.10, 11, 300, 11, random_seed=0
)

spc_tree = SPCTree.construct(spc_labelings)

print(f'SPC tree with nodes: {len(spc_tree)}')

def set_centroid(node):
	node.centroid = X[node.cluster].mean(axis=0)

spc_tree.dfs(lambda node, _: set_centroid(node), None)

print('Set centroids.')

def calc_link_weight(
		n1: SPCTree, 										# Node 1
		n2: SPCTree, 										# Node 2
		sig_s: float,										# Sigmoid slope
		sig_k: float,  									# Sigmoid offset
	) -> float:
	'''
	Calculate a link's weight.
	'''
	# Distance between centroids
	d = np.linalg.norm(n1.centroid - n2.centroid)
	# Scaled distance
	a = np.exp(-(d - sig_k) / sig_s)
	# Sigmoid
	return a / (1 + a)

def visit_link(node1, node2):
	calc_link_weight(node1, node2, 0.005, 0.03)

profiler = cProfile.Profile()
try:
	print('Profiling...')
	profiler.enable()
	spc_tree.dfs(
		lambda node1, acc1: spc_tree.dfs(
			lambda node2, acc2: visit_link(node1, node2),
			acc1
		),
		None
	)
	profiler.disable()
except:
	traceback.print_exc()
	print('Terminated prematurely.')
print('Done.')

stats = pstats.Stats(profiler).sort_stats('tottime')
stats.print_stats(40)