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
	'spc',
	'spc_segfuse',
	'overall',
]

seconds = np.array([
	[65.566850, 50.045283, 0.000967, 7.073463, 1542.168350, 92.905246, 1291.721091, 81.981147, 1635.077864],
	[36.564878, 24.711597, 0.000621, 3.714342, 900.670415, 89.372415, 668.375024, 83.217426, 990.048208],
	[34.108956, 21.543571, 0.000640, 3.335596, 706.663972, 80.478448, 535.879915, 89.710905, 787.149108],
]).T

percentage = seconds / seconds[-1]

fig1, ax1 = plt.subplots()
plt.suptitle(f'fast-spc ({data_length} / {data_size})', fontsize=20)
ax1.set_xlabel('# processes')
ax1.set_ylabel('Time (seconds)')

for i in range(len(stages)):
	ax1.plot(processes, seconds[i], label=stages[i])

matplotx.line_labels()

fig2, ax2 = plt.subplots()
plt.suptitle(f'fast-spc ({data_length} / {data_size})', fontsize=20)
ax2.set_xlabel('# processes')
ax2.set_ylabel('Time (percentage)')

for i in range(len(stages)):
	ax2.plot(processes, percentage[i], label=stages[i])

matplotx.line_labels()
plt.tight_layout()
plt.show()