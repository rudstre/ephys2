'''
Table to rST code adapted from 
https://stackoverflow.com/questions/11347505/what-are-some-approaches-to-outputting-a-python-data-structure-to-restructuredte
'''

import pandas as pd
import numpy as np
import pdb

def df_to_rst(df: pd.DataFrame, with_index: bool=True) -> str:
  header = np.array(([str(df.index.name)] if with_index else []) + df.columns.tolist())
  values = np.hstack((np.array(df.index)[:, np.newaxis], df.values)) if with_index else df.values
  grid = np.vstack((header, values))
  grid = np.vectorize(str)(grid)
  grid = grid.tolist()

  max_cols = [max(out) for out in map(list, zip(*[[len(item) for item in row] for row in grid]))]
  rst = table_div(max_cols, 1)

  for i, row in enumerate(grid):
    header_flag = False
    if i == 0 or i == len(grid)-1: header_flag = True
    rst += normalize_row(row,max_cols)
    rst += table_div(max_cols, header_flag )
  return rst

def table_div(max_cols, header_flag=1) -> str:
  out = ""
  if header_flag == 1:
    style = "="
  else:
    style = "-"

  for max_col in max_cols:
    out += max_col * style + " "

  out += "\n"
  return out

def normalize_row(row, max_cols) -> str:
  r = ""
  for i, max_col in enumerate(max_cols):
    r += row[i] + (max_col  - len(row[i]) + 1) * " "
  return r + "\n"