import numpy as np
import matplotlib.pyplot as plt
import matplotx

data_length = '3 hours'
data_size = '81G'

processes = np.array([
	16,
	32,
	40,
])

stages = [
	'bandpass',
	'median_filter',
	'set_zero',
	'fast_threshold',
	'evaluation',
	'serialization',
	'isosplit_segfuse',
	'overall',
]

seconds = np.array([
	[70.491534, 51.213168, 0.001062, 7.552112, 327.997081, 132.726132, 162.457621, 460.749966],
	[35.705246, 24.711597, 0.000579, 3.667334, 234.133161, 156.687612, 91.176084, 390.821362],
	[34.578881, 20.812385, 0.000530, 3.305012, 165.241890, 144.741833, 74.872960, 309.984435],
]).T

percentage = seconds / seconds[-1]

fig1, ax1 = plt.subplots()
plt.suptitle(f'fast-isosplit ({data_length} / {data_size})', fontsize=20)
ax1.set_xlabel('# processes')
ax1.set_ylabel('Time (seconds)')

for i in range(len(stages)):
	ax1.plot(processes, seconds[i], label=stages[i])

matplotx.line_labels()
	
fig2, ax2 = plt.subplots()
plt.suptitle(f'fast-isosplit ({data_length} / {data_size})', fontsize=20)
ax2.set_xlabel('# processes')
ax2.set_ylabel('Time (percentage)')

for i in range(len(stages)):
	ax2.plot(processes, percentage[i], label=stages[i])

matplotx.line_labels()
plt.tight_layout()
plt.show()