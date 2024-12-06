
from typing import Tuple
import matplotlib.pyplot as plt
import tkinter

def px_figsize(pxx: int, pxy: int) -> Tuple[float, float]:
	px = 1/plt.rcParams['figure.dpi'] # pixel in inches
	return (pxx*px, pxy*px)

def max_figsize(margin_x=10, margin_y=80) -> Tuple[float, float]:
	root = tkinter.Tk()
	root.withdraw()
	w, h = root.winfo_screenwidth(), root.winfo_screenheight()
	return px_figsize(w-margin_x, h-margin_y)

def signalplot(n_signals: int):
	assert n_signals > 0
	plt.rcParams['lines.linewidth'] = 0.5
	fig, axs = plt.subplots(n_signals, 1, sharex=True, figsize=max_figsize(), constrained_layout=True)
	fig.set_constrained_layout_pads(hspace=0.0, h_pad=0.0) 
	axs[0].ticklabel_format(useOffset=False, style='plain')
	for ax in axs[:-1]:
		ax.tick_params(axis='x', which='both', bottom=False) # turn off major & minor ticks on the bottom
	return fig, axs