'''
Color schemes for ephys2 gui
'''

import colorcet as cc
import numpy as np
import pyqtgraph as pg

'''
Constants
'''

wide_width = 4
secondary_alpha = 50

colorwheel_rgb = cc.glasbey_bw_minc_20_maxl_70
colorwheel_hex = cc.glasbey_dark
n_colors = len(colorwheel_rgb)

'''
Pens
'''

primary_pens = np.array([pg.mkPen(int(r*255), int(g*255), int(b*255)) for r, g, b in colorwheel_rgb])
primary_pens_wide = np.array([pg.mkPen(int(r*255), int(g*255), int(b*255), width=wide_width) for r, g, b in colorwheel_rgb])

secondary_pens = np.array([pg.mkPen(int(r*255), int(g*255), int(b*255), secondary_alpha) for r, g, b in colorwheel_rgb]) 

'''
Brushes
'''

primary_brushes = np.array([pg.mkBrush(int(r*255), int(g*255), int(b*255)) for r, g, b in colorwheel_rgb]) 

secondary_brushes = np.array([pg.mkBrush(int(r*255), int(g*255), int(b*255), secondary_alpha) for r, g, b in colorwheel_rgb]) 
