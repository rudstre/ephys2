import numpy as np
from scipy import stats
import matplotlib.pyplot as plt

betas = np.logspace(0, 2, 10)
x = np.linspace(0, 1, 1000)

for beta in betas:
	y = stats.beta.pdf(x, beta, beta)
	plt.plot(x, y, label=str(beta))

plt.legend()
plt.tight_layout()
plt.show()