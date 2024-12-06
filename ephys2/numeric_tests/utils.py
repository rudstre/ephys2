'''
Package-wide common utilities.
'''

import pdb
import pandas as pd
import colorcet as cc
from bokeh.io import show
from bokeh.models import ColumnDataSource, DataTable, TableColumn

from ephys2.lib.types import *

def show_df(df: pd.DataFrame):
	''' See https://stackoverflow.com/questions/35634238/how-to-save-a-pandas-dataframe-table-as-a-png ''' 
	source = ColumnDataSource(df)
	df_columns = [df.index.name]
	df_columns.extend(df.columns.values)
	columns_for_table=[]
	for column in df_columns:
		columns_for_table.append(TableColumn(field=column, title=column))

	width = len(''.join(df_columns)) * 10
	data_table = DataTable(source=source, columns=columns_for_table,height_policy="auto",width=width,index_position=None)
	show(data_table)

def get_clustering_colors(size: int, clustering: Clustering) -> List[str]:
	cs = ['black'] * size
	N = len(cc.glasbey)
	for i, cluster in enumerate(clustering):
		for j in cluster:
			cs[j] = cc.glasbey[i % N] # only 256 colors available, but still give the illusion of separation
	return cs 

def get_labeling_colors(indices: Labeling) -> List[str]:
	N = len(cc.glasbey)
	return [cc.glasbey[i % N] for i in indices] # only 256 colors available, but still give the illusion of separation

