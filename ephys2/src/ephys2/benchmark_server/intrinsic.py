'''
Intrinsic benchmarks application
'''
from dash import Dash, html, dcc
import plotly.express as px
import plotly.graph_objs as go
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np
from typing import List

from ephys2.pipeline.benchmark.intrinsic import *

def intrinsic_benchmarks_app(benchmarks: List[IntrinsicBenchmark]) -> Dash:
	N = len(benchmarks)

	app = Dash(__name__)
	app.layout = html.Div(children=[
		html.H1(children='Ephys2 intrinsic benchmarks'),
		html.Div(children=f'Dataset: {benchmarks[0].dataset}'),
		dcc.Graph(id='0', figure=go.Figure(go.Indicator(
			mode = 'number', value = 
		)))
	])

	return app

