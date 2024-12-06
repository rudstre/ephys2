'''
Extrinsic benchmarks application
'''
from dash import Dash, html, dcc
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List

from ephys2.pipeline.benchmark.extrinsic import *

def extrinsic_benchmarks_app(benchmarks: List[ExtrinsicBenchmark]) -> Dash:
	N = len(benchmarks)

	app = Dash(__name__)

	pair_CMs_div = make_confmat_row([(np.log10(np.array(bm.pair_CM) + 1e-3), f'Pair confusion matrix ({bm.method}) [log10 scale]') for bm in benchmarks])
	full_CMs_div = make_confmat_row([(np.log10(np.array(bm.full_CM) + 1e-3), f'Full confusion matrix ({bm.method}) [log10 scale]') for bm in benchmarks])
	matched_CMs_div = make_confmat_row([(np.log10(np.array(bm.matched_CM) + 1e-3), f'Matched confusion matrix ({bm.method}) [log10 scale]') for bm in benchmarks])

	overall_df = pd.DataFrame({
		'Method': [bm.method for bm in benchmarks],
		'Accuracy (full)': [bm.full_accuracy for bm in benchmarks],
		'Accuracy (matched)': [bm.matched_accuracy for bm in benchmarks],
		'Homogeneity (full)': [bm.full_homogeneity for bm in benchmarks],
		'Homogeneity (matched)': [bm.matched_homogeneity for bm in benchmarks],
		'Completeness (full)': [bm.full_completeness for bm in benchmarks],
		'Completeness (matched)': [bm.matched_completeness for bm in benchmarks],
		'Adjusted Rand Index': [bm.adj_rand_index for bm in benchmarks],
		'False positive rate (FP / (FP + TP + TN))': [bm.false_positive_rate for bm in benchmarks],
		'False negative rate (FN / (FN + TP + TN))': [bm.false_negative_rate for bm in benchmarks]
	})

	overall_figs = []
	for col in overall_df.columns:
		if col != 'Method':
			fig = px.bar(overall_df, y="Method", x=col, orientation='h')
			fig.update_xaxes(range=[0.,1.])
			fig.update_traces(width=0.2)
			# fig.update_layout(margin=go.layout.Margin(l=0,r=0,t=0,b=0))
			overall_figs.append(fig)

	precision_gr = make_perunit_fig('Precision', benchmarks, lambda bm: bm.precision)
	recall_gr = make_perunit_fig('Recall', benchmarks, lambda bm: bm.recall)

	app.layout = html.Div(children=[
		html.H1(children='Ephys2 extrinsic benchmarks'),
		html.Div(children=f'Dataset: {benchmarks[0].dataset}'),
		pair_CMs_div,
		full_CMs_div,
		matched_CMs_div,
	] + 
	[
		dcc.Graph(
			id=f'overall_figs_{i}',
			figure=fig
		)
		for i, fig in enumerate(overall_figs)
	] + [
		precision_gr,
		recall_gr
	])

	return app

def make_confmat_row(cms_and_titles: List[Tuple[ConfusionMatrix, str]]) -> html.Div:
	hms_div = []
	for C, title in cms_and_titles:
		hm_fig = px.imshow(C, text_auto=True)
		hm_fig.update_yaxes(visible=False, showticklabels=False)
		hm_fig.update_xaxes(visible=False, showticklabels=False)
		hm_fig.update_layout(title_text=title)
		hm_div = html.Div(children=[dcc.Graph(
			id=title,
			figure=hm_fig
		)], style={'display': 'inline-block'})
		hms_div.append(hm_div)
	hms_div = html.Div(children=hms_div, style={'width': '100%', 'display': 'inline-block'})
	return hms_div

def make_perunit_fig(name: str, bms: List[ExtrinsicBenchmark], get_data: Callable) -> dcc.Graph:
	df = {
		'Method': [],
		'Unit': [],
		name: [],
	}

	for bm in bms:
		data = np.array(get_data(bm))
		assert len(data.shape) == 1
		N = data.size
		df['Method'].append(np.full(N, bm.method))
		df['Unit'].append(np.arange(N))
		df[name].append(data)

	df['Method'] = np.hstack(df['Method'])
	df['Unit'] = np.hstack(df['Unit'])
	df[name] = np.hstack(df[name])
	df = pd.DataFrame(df)

	fig = px.bar(df, y=name, x='Unit', facet_col='Method')
	fig.update_yaxes(matches=None, showticklabels=True)
	gr = dcc.Graph(
		id=f'per_unit_{name}',
		figure=fig
	)
	return gr

