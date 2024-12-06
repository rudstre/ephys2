'''
Unit tests of SPC segmentation fusion stage
'''

from typing import List
import numpy as np

from ephys2.lib.types import *
from ephys2.lib.spc import *
from ephys2.pipeline.label_old.spc_segfuse import *

def list2clus(ls: List[int]) -> Cluster:
	return np.array(ls, dtype=np.int64)

def test_node_weight_1():
	tree = SPCTree(
		cluster=list2clus([1,2,3,4]),
		children=[
			SPCTree(
				cluster=list2clus([1]),
				children=[]
			),
			SPCTree(
				cluster=list2clus([2,3,4]),
				children=[
					SPCTree(
						cluster=list2clus([2,3]),
						children=[]
					),
					SPCTree(
						cluster=list2clus([4]),
						children=[]
					)
				]
			)
		]
	)

	assert calc_node_weight(tree) == 4 / (4 + 3 + 2)
	assert calc_node_weight(tree.children[0]) == 1
	assert calc_node_weight(tree.children[1]) == 3 / (3 + 2)
	assert calc_node_weight(tree.children[1].children[0]) == 1


